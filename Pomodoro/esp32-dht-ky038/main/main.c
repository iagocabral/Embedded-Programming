#include <stdio.h>
#include <string.h>
#include "nvs_flash.h"
#include "esp_wifi.h"
#include "esp_event.h"
#include "esp_http_client.h"
#include "esp_log.h"
#include "freertos/semphr.h"
#include <dht.h>

#include "driver/gpio.h"
#include "esp_adc/adc_oneshot.h"
#include "esp_log.h"
#include "esp_sleep.h"

#include "wifi.h"
#include "mqtt.h"

SemaphoreHandle_t conexaoWifiSemaphore;
SemaphoreHandle_t conexaoMQTTSemaphore;

const int dht_gpio = 18;
const int ADC_PIN = 4;
const int DO_PIN = 5;
#define LIMITE_DB 600

#define SENSOR_TYPE DHT_TYPE_DHT11

// Função para modo bateria com deep sleep
void enter_deep_sleep_mode() {
    const int sleep_time_sec = 10;
    esp_sleep_enable_timer_wakeup(sleep_time_sec * 1500000);
    esp_deep_sleep_start();
}

void sensor_ky037(void *pvParameters) {
    adc_oneshot_unit_handle_t adc1_handle;
    adc_oneshot_unit_init_cfg_t init_config = {
        .unit_id = ADC_UNIT_1,
    };
    adc_oneshot_new_unit(&init_config, &adc1_handle);

    adc_oneshot_chan_cfg_t config = {
        .atten = ADC_ATTEN_DB_0,
        .bitwidth = ADC_BITWIDTH_DEFAULT,
    };
    adc_oneshot_config_channel(adc1_handle, ADC_PIN, &config);

    gpio_set_direction(DO_PIN, GPIO_MODE_INPUT);

    char mensagem[50];
    while (1) {
        // Lê os valores do sensor
        int adc_value = 0;
        adc_oneshot_read(adc1_handle, ADC_PIN, &adc_value);
        sprintf(mensagem, "{\"valorSomAnalogico\": %d}", adc_value);
        mqtt_envia_mensagem("v1/devices/me/telemetry", mensagem);

        int digital_value = gpio_get_level(DO_PIN);
        
        // printf("Limite de som configurado no sensor excedido (Saída Digital).\n");
        sprintf(mensagem, "{\"valorSomDigital\": %d}", digital_value);
        mqtt_envia_mensagem("v1/devices/me/attributes", mensagem);

        vTaskDelay(pdMS_TO_TICKS(3000));
    }   
    // Apaga a configuração do ADC se a função terminar (no modo energia, isso nunca ocorrerá)
    adc_oneshot_del_unit(adc1_handle);
}

#define SENSOR_TYPE DHT_TYPE_DHT11
void sensor_dht(void *pvParameters) {
        float temperature, humidity;

    #ifdef CONFIG_EXAMPLE_INTERNAL_PULLUP
        gpio_set_pull_mode(dht_gpio, GPIO_PULLUP_ONLY);
    #endif
        char mensagem[50];
        if(xSemaphoreTake(conexaoMQTTSemaphore, portMAX_DELAY)) {
            while(true) {
                if (dht_read_float_data(SENSOR_TYPE, dht_gpio, &humidity, &temperature) == ESP_OK) {
                    sprintf(mensagem, "{\"tempDHT\": %f}", temperature);
                    mqtt_envia_mensagem("v1/devices/me/telemetry", mensagem);

                    sprintf(mensagem, "{\"humidDHT\": %f}", humidity);
                    mqtt_envia_mensagem("v1/devices/me/telemetry", mensagem);
                } else {
                    printf("Could not read data from sensor\n");
                }

                vTaskDelay(10000 / portTICK_PERIOD_MS);
            }
        }
}

void conectadoWifi(void * params) {
    while(true) {
        if(xSemaphoreTake(conexaoWifiSemaphore, portMAX_DELAY)) {
            // Processamento Internet
            mqtt_start();
        }
    }
}

void trataComunicacaoComServidor(void * params) {
    char mensagem[50];
    if(xSemaphoreTake(conexaoMQTTSemaphore, portMAX_DELAY)) {
        while(true) {
            float temperatura = 20.0 + (float)rand()/(float)(RAND_MAX/10.0);
            sprintf(mensagem, "temperatura1: %f", temperatura);
            // mqtt_envia_mensagem("v1/devices/me/telemetry", mensagem);

            sprintf(mensagem, "humidade: %d", 5);
            // mqtt_envia_mensagem("v1/devices/me/attributes", mensagem);
            vTaskDelay(3000 / portTICK_PERIOD_MS);
        }
    }
}

void app_main(void) {
    // Inicializa o NVS
    esp_err_t ret = nvs_flash_init();
    if (ret == ESP_ERR_NVS_NO_FREE_PAGES || ret == ESP_ERR_NVS_NEW_VERSION_FOUND) {
      ESP_ERROR_CHECK(nvs_flash_erase());
      ret = nvs_flash_init();
    }
    ESP_ERROR_CHECK(ret);
    
    conexaoWifiSemaphore = xSemaphoreCreateBinary();
    conexaoMQTTSemaphore = xSemaphoreCreateBinary();
    wifi_start();

    // Verifica o modo de operação
    #ifdef CONFIG_MODO_BATERIA
        xTaskCreate(&conectadoWifi,  "Conexão ao MQTT", 4096, NULL, 1, NULL);
        xTaskCreate(&trataComunicacaoComServidor, "Comunicação com Broker", 4096, NULL, 1, NULL);
        xTaskCreate(&sensor_ky037, "sensor_ky037", configMINIMAL_STACK_SIZE * 3, NULL, 5, NULL);
        
        // Aguarda 15 segundos e entra em deep sleep
        vTaskDelay(pdMS_TO_TICKS(1000));
        printf("Entrando em modo de economia de energia por 15 segundos\n");
        enter_deep_sleep_mode();
    #else
        // Modo energia (sem sleep)
        xTaskCreate(&conectadoWifi,  "Conexão ao MQTT", 4096, NULL, 1, NULL);
        xTaskCreate(&trataComunicacaoComServidor, "Comunicação com Broker", 4096, NULL, 1, NULL);
        xTaskCreate(&sensor_dht, "sensor_dht", configMINIMAL_STACK_SIZE * 3, NULL, 5, NULL);
        xTaskCreate(&sensor_ky037, "sensor_ky037", configMINIMAL_STACK_SIZE * 3, NULL, 5, NULL);
    #endif
}