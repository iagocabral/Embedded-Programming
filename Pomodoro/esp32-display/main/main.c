#include <stdio.h>
#include <string.h>
#include "nvs_flash.h"
#include "esp_wifi.h"
#include "esp_event.h"
#include "esp_http_client.h"
#include "esp_log.h"
#include "freertos/semphr.h"

#include "wifi.h"
#include "mqtt.h"
#include "bttm.h"
#include "oled.h"

SemaphoreHandle_t conexaoWifiSemaphore;
SemaphoreHandle_t conexaoMQTTSemaphore;

SemaphoreHandle_t bttmSemaphore;

bool button = false;

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
  char tempo[50];
  bool last_state = false;
  if(xSemaphoreTake(conexaoMQTTSemaphore, portMAX_DELAY))
  {
    while(true)
    {

      bool oled_state = get_state();
      
      printf("Estado do botão: %d\n", oled_state);
      if(last_state != oled_state){
        sprintf(mensagem, "{\"state_timer\": %d}", oled_state);
        mqtt_envia_mensagem(client, "v1/devices/me/telemetry", mensagem);
        mqtt_envia_mensagem(client2, "unb_fse/led_color", mensagem);
}
      int time = get_time();
      printf("Estado do timer: %d\n", time);
      sprintf(tempo, "{\"timer_foco\": %d}", time );
      mqtt_envia_mensagem(client,"v1/devices/me/telemetry", tempo);

      time = get_inter();
      printf("Estado do timer inter: %d\n", time);
      sprintf(tempo, "{\"timer_inter\": %d}", time );
      mqtt_envia_mensagem(client,"v1/devices/me/telemetry", tempo);

      vTaskDelay(1000 / portTICK_PERIOD_MS);
      last_state = oled_state;
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
    bttmSemaphore = xSemaphoreCreateBinary();

    wifi_start();

    xTaskCreate(&conectadoWifi,  "Conexão ao MQTT", 4096, NULL, 1, NULL);
    xTaskCreate(&trataComunicacaoComServidor, "Comunicação com Broker", 4096, NULL, 1, NULL);
    xTaskCreate(&display, "Leitura do Oled", 4096, NULL, 1, NULL); // Higher priority
    

}