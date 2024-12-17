#include <stdio.h>
#include <stdint.h>
#include <stddef.h>
#include <string.h>
#include "esp_system.h"
#include "esp_event.h"
#include "esp_netif.h"

#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/semphr.h"
#include "freertos/queue.h"

#include "lwip/sockets.h"
#include "lwip/dns.h"
#include "lwip/netdb.h"

#include "esp_log.h"
#include "mqtt_client.h"
#include "cJSON.h"

#include "mqtt.h"
#include "buzzer.h"

#define TAG "MQTT"

extern SemaphoreHandle_t conexaoMQTTSemaphore;
esp_mqtt_client_handle_t client;
esp_mqtt_client_handle_t client2;

void process_led_state(const char *data, int data_len) {
    // Parse o JSON recebido
    cJSON *json = cJSON_Parse(data);
    if (json == NULL) {
        ESP_LOGE("BUTTON_STATE", "Erro ao parsear JSON");
        return;
    }

    // Extrair o valor do estado do botão
    cJSON *state_timer = cJSON_GetObjectItem(json, "state_timer");
    if (state_timer == NULL || cJSON_IsString(state_timer)) {
        ESP_LOGE("BUTTON_STATE", "Erro ao extrair 'button_state' ou 'button_state' não é uma string");
        cJSON_Delete(json);
        return;
    }

    // Converte o valor de string para número
    int state = state_timer->valueint;

    // Loga o estado do botão
    ESP_LOGI("BUTTON_STATE", "Estado do botão capturado: %d", state);

    // Muda a cor do LED RGB com base no estado do botão
   if (state == 1) {
        buzzer_init();
        play_timer_buzzer();
    } else if (state == 2) {
        buzzer_init();
        play_timer_buzzer();
    } else {
        ESP_LOGI("RGB_COLOR", "Estado do botão não reconhecido: %d", state);
    }

    // Limpar o objeto JSON
    cJSON_Delete(json);
}

static void log_error_if_nonzero(const char *message, int error_code)
{
    if (error_code != 0) {
        ESP_LOGE(TAG, "Last error %s: 0x%x", message, error_code);
    }
}

void processar_comando(const char *data)
{
    // Parseia o JSON recebido
    cJSON *json = cJSON_Parse(data);
    if (json == NULL)
    {
        ESP_LOGE(TAG, "Erro ao parsear o JSON");
        return;
    }

    // Extrai o campo "params"
    cJSON *params = cJSON_GetObjectItem(json, "params");
    if (params == NULL)
    {
        ESP_LOGE(TAG, "Campo 'params' não encontrado no JSON");
        cJSON_Delete(json);
        return;
    }

    // Verifica se o campo "luz" é true
    cJSON *luz = cJSON_GetObjectItem(params, "luz");
    if (cJSON_IsBool(luz) && cJSON_IsTrue(luz))
    {
        ESP_LOGI(TAG, "Luz ativada! Tocando música de Star Wars.");
        play_timer_buzzer();
    }
    else
    {
        ESP_LOGI(TAG, "Comando 'luz' não é verdadeiro ou não encontrado.");
    }

    cJSON_Delete(json);
}

static void mqtt_event_handler(void *handler_args, esp_event_base_t base, int32_t event_id, void *event_data)
{
    ESP_LOGD(TAG, "Event dispatched from event loop base=%s, event_id=%d", base, (int) event_id);
    esp_mqtt_event_handle_t event = event_data;
    esp_mqtt_client_handle_t client = event->client;
    int msg_id;
    switch ((esp_mqtt_event_id_t)event_id) {
    case MQTT_EVENT_CONNECTED:
        ESP_LOGI(TAG, "MQTT_EVENT_CONNECTED");
        xSemaphoreGive(conexaoMQTTSemaphore);
        msg_id = esp_mqtt_client_subscribe(client, "v1/devices/me/rpc/request/+", 0);
        break;
    case MQTT_EVENT_DISCONNECTED:
        ESP_LOGI(TAG, "MQTT_EVENT_DISCONNECTED");
        break;

    case MQTT_EVENT_SUBSCRIBED:
        ESP_LOGI(TAG, "MQTT_EVENT_SUBSCRIBED, msg_id=%d", event->msg_id);
        msg_id = esp_mqtt_client_publish(client, "/topic/qos0", "data", 0, 0, 0);
        ESP_LOGI(TAG, "sent publish successful, msg_id=%d", msg_id);
        break;
    case MQTT_EVENT_UNSUBSCRIBED:
        ESP_LOGI(TAG, "MQTT_EVENT_UNSUBSCRIBED, msg_id=%d", event->msg_id);
        break;
    case MQTT_EVENT_PUBLISHED:
        ESP_LOGI(TAG, "MQTT_EVENT_PUBLISHED, msg_id=%d", event->msg_id);
        break;
    case MQTT_EVENT_DATA:
        ESP_LOGI(TAG, "MQTT_EVENT_DATA");
        printf("TOPIC=%.*s\r\n", event->topic_len, event->topic);
        printf("DATA=%.*s\r\n", event->data_len, event->data);
        processar_comando(event->data);
        break;
    case MQTT_EVENT_ERROR:
        ESP_LOGI(TAG, "MQTT_EVENT_ERROR");
        if (event->error_handle->error_type == MQTT_ERROR_TYPE_TCP_TRANSPORT) {
            log_error_if_nonzero("reported from esp-tls", event->error_handle->esp_tls_last_esp_err);
            log_error_if_nonzero("reported from tls stack", event->error_handle->esp_tls_stack_err);
            log_error_if_nonzero("captured as transport's socket errno",  event->error_handle->esp_transport_sock_errno);
            ESP_LOGI(TAG, "Last errno string (%s)", strerror(event->error_handle->esp_transport_sock_errno));

        }
        break;
    default:
        ESP_LOGI(TAG, "Other event id:%d", event->event_id);
        break;
    }
}

static void mqtt_event_handler2(void *handler_args, esp_event_base_t base, int32_t event_id, void *event_data)
{
    esp_mqtt_event_handle_t event = event_data;
    switch (event->event_id) {
        case MQTT_EVENT_CONNECTED:
            ESP_LOGI("MQTT2", "Conectado ao broker público Mosquitto");
            esp_mqtt_client_subscribe(client2, "unb_fse/led_color", 0);
            break;
        case MQTT_EVENT_DATA:
            ESP_LOGI("MQTT", "Mensagem recebida: %.*s", event->data_len, event->data);

            // Processa o dado recebido do botão
            process_led_state(event->data, event->data_len);
            break;
        default:
            break;
    }
}

void mqtt_start()
{
    esp_mqtt_client_config_t mqtt_config = {
        .broker.address.uri = "mqtt://164.41.98.25",
        .credentials.username = "EBuR93tDJtrB87koLOry"
    };

    client = esp_mqtt_client_init(&mqtt_config);
    esp_mqtt_client_register_event(client, ESP_EVENT_ANY_ID, mqtt_event_handler, NULL);
    esp_mqtt_client_start(client);

    esp_mqtt_client_config_t mqtt_config2 = {
        .broker.address.uri = "mqtt://test.mosquitto.org"
    };
    client2 = esp_mqtt_client_init(&mqtt_config2);
    esp_mqtt_client_register_event(client2, ESP_EVENT_ANY_ID, mqtt_event_handler2, NULL);
    esp_mqtt_client_start(client2);
}

void mqtt_envia_mensagem(esp_mqtt_client_handle_t client, char * topico, char * mensagem)
{
    int message_id = esp_mqtt_client_publish(client, topico, mensagem, 0, 1, 0);
    ESP_LOGI(TAG, "Mesnagem enviada, ID: %d", message_id);
}



