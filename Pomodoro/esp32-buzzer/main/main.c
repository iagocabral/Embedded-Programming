#include <stdio.h>
#include <string.h>
#include "nvs_flash.h"
#include "esp_wifi.h"
#include "esp_event.h"
#include "esp_log.h"
#include "freertos/semphr.h"
#include "wifi.h"
#include "mqtt.h"
#include "buzzer.h"


SemaphoreHandle_t conexaoWifiSemaphore;
SemaphoreHandle_t conexaoMQTTSemaphore;

void conectadoWifi(void * params)
{
  while(true)
  {
    if(xSemaphoreTake(conexaoWifiSemaphore, portMAX_DELAY))
    {
      // Processamento Internet
      mqtt_start();
    }
  }
}

void trataComunicacaoComServidor(void * params)
{
  char mensagem[50];
  if(xSemaphoreTake(conexaoMQTTSemaphore, portMAX_DELAY))
  {
    while(true)
    {
       int temperatura = 10;
       
      sprintf(mensagem, "{\"temperatura1\": %d}", temperatura);
      mqtt_envia_mensagem(client, "v1/devices/me/telemetry", mensagem);

      sprintf(mensagem, "{\"humidade\": %d}", 5);
      mqtt_envia_mensagem(client, "v1/devices/me/attributes", mensagem);
      vTaskDelay(3000 / portTICK_PERIOD_MS);
    }
  }
}

void app_main(void)
{
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

    xTaskCreate(&conectadoWifi,  "Conexão ao MQTT", 4096, NULL, 1, NULL);
    xTaskCreate(&trataComunicacaoComServidor, "Comunicação com Broker", 4096, NULL, 1, NULL);

    // Inicializa o buzzer
    // buzzer_init();
    // Toca a melodia do Star Wars
    // play_star_wars_theme();
}