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

#include "mqtt.h"
#include "button.h"
#include "rgb.h"

#include "cJSON.h"

#define TAG "MQTT"

extern SemaphoreHandle_t conexaoMQTTSemaphore;
extern SemaphoreHandle_t pomodoroSemaphore;

esp_mqtt_client_handle_t client1 = NULL;
esp_mqtt_client_handle_t client2 = NULL;

void log_enviada_public(const char *topico, const char *mensagem) {
    ESP_LOGI("MQTT_PUB", "Mensagem enviada para o broker público Mosquitto\nTópico: %s\nMensagem: %s", topico, mensagem);
}

void process_mqtt_data(const char* data) {
    // Parse o JSON recebido
    cJSON *json = cJSON_Parse(data);
    if (json == NULL) {
        ESP_LOGE(TAG, "Erro ao parsear JSON");
        return;
    }

    // Extrair o valor de "method"
    cJSON *method = cJSON_GetObjectItem(json, "method");
    if (method == NULL || !cJSON_IsString(method)) {
        ESP_LOGE(TAG, "Erro ao extrair 'method' do JSON ou 'method' não é uma string");
        cJSON_Delete(json);
        return;
    }

    // Extrair o valor de "params"
    cJSON *params = cJSON_GetObjectItem(json, "params");
    if (params == NULL || !cJSON_IsBool(params)) {
        ESP_LOGE(TAG, "Erro ao extrair 'params' do JSON ou 'params' não é um booleano");
        cJSON_Delete(json);
        return;
    }

    // Verificar se "method" é "setValue" e "params" é true
    if (strcmp(method->valuestring, "setValue") == 0 && cJSON_IsTrue(params)) {
        ESP_LOGI(TAG, "'method' é 'setValue' e 'params' é true, chamando a função apropriada...");
        xSemaphoreGive(pomodoroSemaphore);
    } else {
        ESP_LOGI(TAG, "'method' não é 'setValue' ou 'params' não é true, nada a fazer.");
        send_led_color(0);
        xSemaphoreGive(pomodoroSemaphore);
    }

    // Limpar o objeto JSON
    cJSON_Delete(json);
}

void process_led_state(const char *data, int data_len) {
    cJSON *json = cJSON_Parse(data);
    if (json == NULL) {
        ESP_LOGE("BUTTON_STATE", "Erro ao parsear JSON");
        return;
    }

    cJSON *state_timer = cJSON_GetObjectItem(json, "state_timer");
    if (state_timer == NULL || !cJSON_IsNumber(state_timer)) { 
        ESP_LOGE("BUTTON_STATE", "Erro ao extrair 'state_timer' ou 'state_timer' não é um número");
        cJSON_Delete(json);
        return;
    }

    int state = state_timer->valueint;


    ESP_LOGI("BUTTON_STATE", "Estado do botão capturado: %d", state);

    if (state == 0) {
        // Azul
        if(button_state == 0) {
            send_led_color(0);
        } else{
            send_led_color(3);  
            set_rgb_color(255, 255, 0);
            ESP_LOGI("RGB_COLOR", "Cor definida: Azul");
        }
    } else if (state == 1) {
        // Vermelho
        set_rgb_color(0, 255, 255);
        ESP_LOGI("RGB_COLOR", "Cor definida: Vermelho");
        send_led_color(1);
    } else if (state == 2) {
        // Verde
        set_rgb_color(255, 0, 255);
        ESP_LOGI("RGB_COLOR", "Cor definida: Verde");
        send_led_color(2);
    } else {
        ESP_LOGI("RGB_COLOR", "Estado do botão não reconhecido: %d", state);
    }

    // Limpar o objeto JSON
    cJSON_Delete(json);
}

static void mqtt_event_handler(void *handler_args, esp_event_base_t base, int32_t event_id, void *event_data)
{
    ESP_LOGD(TAG, "Event dispatched from event loop base=%s, event_id=%d", base, (int) event_id);
    esp_mqtt_event_handle_t event = event_data;
    esp_mqtt_client_handle_t client1 = event->client;
    int msg_id = -1;

    switch ((esp_mqtt_event_id_t)event_id) {
    case MQTT_EVENT_CONNECTED:
        ESP_LOGI(TAG, "MQTT_EVENT_CONNECTED");
        xSemaphoreGive(conexaoMQTTSemaphore);
        msg_id = esp_mqtt_client_subscribe(client1, "v1/devices/me/rpc/request/+", 0);
        break;
    case MQTT_EVENT_DISCONNECTED:
        ESP_LOGI(TAG, "MQTT_EVENT_DISCONNECTED");
        break;
    case MQTT_EVENT_SUBSCRIBED:
        ESP_LOGI(TAG, "MQTT_EVENT_SUBSCRIBED, msg_id=%d", event->msg_id);
        msg_id = esp_mqtt_client_publish(client1, "/topic/qos0", "data", 0, 0, 0);
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
        process_mqtt_data(event->data);
        break;
    case MQTT_EVENT_ERROR:
        ESP_LOGI(TAG, "MQTT_EVENT_ERROR");
        if (event->error_handle->error_type == MQTT_ERROR_TYPE_TCP_TRANSPORT) {
            // log_error_if_nonzero("reported from esp-tls", event->error_handle->esp_tls_last_esp_err);
            // log_error_if_nonzero("reported from tls stack", event->error_handle->esp_tls_stack_err);
            // log_error_if_nonzero("captured as transport's socket errno",  event->error_handle->esp_transport_sock_errno);
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
                process_led_state(event->data, event->data_len);
                ESP_LOGI("MQTT", "Estado alterado, processando nova mensagem.");
            break;
        default:
            break;
    }
}

void mqtt_start()
{
    esp_mqtt_client_config_t mqtt_config = {
        .broker.address.uri = "mqtt://164.41.98.25",
        .credentials.username = "qB84N2zsJuCTzAT9qUU2"
    };
    client1 = esp_mqtt_client_init(&mqtt_config);
    esp_mqtt_client_register_event(client1, ESP_EVENT_ANY_ID, mqtt_event_handler, NULL);
    esp_mqtt_client_start(client1);
    
    esp_mqtt_client_config_t mqtt_config2 = {
        .broker.address.uri = "mqtt://test.mosquitto.org"
    };
    client2 = esp_mqtt_client_init(&mqtt_config2);
    esp_mqtt_client_register_event(client2, ESP_EVENT_ANY_ID, mqtt_event_handler2, NULL);
    esp_mqtt_client_start(client2);
}

void mqtt_stop()
{
    if (client1 != NULL) {
        esp_mqtt_client_stop(client1);
        esp_mqtt_client_destroy(client1);
        client1 = NULL;
    }
    if (client2 != NULL) {
        esp_mqtt_client_stop(client2);
        esp_mqtt_client_destroy(client2);
        client2 = NULL;
    }
}

void mqtt_envia_mensagem(esp_mqtt_client_handle_t client, char * topico, char * mensagem)
{
    int message_id = esp_mqtt_client_publish(client, topico, mensagem, 0, 1, 0);
    ESP_LOGI(TAG, "Mesnagem enviada, ID: %d", message_id);
}