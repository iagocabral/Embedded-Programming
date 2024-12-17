#include <stdio.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "driver/gpio.h"
#include "nvs_flash.h"
#include "esp_err.h"
#include "wifi.h"
#include "mqtt.h"
#include "rgb.h"
#include "button.h"
#include <unistd.h>

SemaphoreHandle_t conexaoWifiSemaphore;
SemaphoreHandle_t conexaoMQTTSemaphore;
SemaphoreHandle_t pomodoroSemaphore;

void conectadoWifi(void * params) {
  while(true) {
    if(xSemaphoreTake(conexaoWifiSemaphore, portMAX_DELAY)) {
      mqtt_start();
    }
  }
}

void trataComunicacaoComServidor(void * params) {
  if(xSemaphoreTake(conexaoMQTTSemaphore, portMAX_DELAY)) {
    while(true) {
       vTaskDelay(3000 / portTICK_PERIOD_MS);
    }
  }
}

void pomodoro_task(void *pvParameter) {
    send_button_state(0);
    while (1) {
      if (xSemaphoreTake(pomodoroSemaphore, portMAX_DELAY)) {
          send_button_state(1);
          while(true){
            if (xSemaphoreTake(pomodoroSemaphore, portMAX_DELAY)) {
              send_led_color(0);
              send_button_state(0);
              break;
            }

          }

          set_rgb_color(255, 255, 255);
          vTaskDelay(10 / portTICK_PERIOD_MS);
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
    pomodoroSemaphore = xSemaphoreCreateBinary();
    wifi_start();

    // Configura o LEDC para controle do LED RGB
    configure_rgb_channels();

    // Apaga o LED ao iniciar
    set_rgb_color(255, 255, 255);
    
    // Cria as tarefas de conexão WiFi e comunicação com o servidor
    xTaskCreate(&conectadoWifi,  "Conexão ao MQTT", 4096, NULL, 1, NULL);
    xTaskCreate(&trataComunicacaoComServidor, "Comunicação com Broker", 4096, NULL, 1, NULL);
    xTaskCreate(&pomodoro_task, "pomodoro_task", 4096, NULL, 5, NULL);

    // Configura o botão
    button_init();

}