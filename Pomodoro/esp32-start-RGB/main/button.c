#include "button.h"
#include "rgb.h"
#include "mqtt.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/semphr.h"
#include "driver/gpio.h"
#include <stdio.h>
#include "esp_log.h"

#define BUTTON_GPIO GPIO_NUM_0

extern SemaphoreHandle_t pomodoroSemaphore;

void IRAM_ATTR button_isr_handler(void* arg) {
    xSemaphoreGiveFromISR(pomodoroSemaphore, NULL);
}

void button_init(void) {
    gpio_config_t io_conf = {
        .intr_type = GPIO_INTR_NEGEDGE,
        .mode = GPIO_MODE_INPUT,
        .pin_bit_mask = (1ULL << BUTTON_GPIO),
        .pull_up_en = 1,
    };
    gpio_config(&io_conf);

    if (gpio_install_isr_service(0) == ESP_OK) {
        ESP_LOGI("GPIO", "ISR service installed successfully");
    } else {
        ESP_LOGI("GPIO", "ISR service already installed, skipping...");
    }

    gpio_isr_handler_add(BUTTON_GPIO, button_isr_handler, NULL);
}

int button_state = 0;

void send_button_state(int state) {
    button_state = state;
    char payload[50];
    sprintf(payload, "{\"button_state\": \"%d\"}", state);
    mqtt_envia_mensagem(client1, "v1/devices/me/telemetry", payload);

    mqtt_envia_mensagem(client2, "unb_fse/button_state", payload);
    log_enviada_public("unb_fse/button_state", payload);
}

void send_led_color(int color) {
    char payload[50];
    sprintf(payload, "{\"led_color\": \"%d\"}", color);
    mqtt_envia_mensagem(client1, "v1/devices/me/telemetry", payload);
}