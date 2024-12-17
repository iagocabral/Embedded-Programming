#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "esp_log.h"
#include "driver/gpio.h"

#include "ssd1306.h"
#include "font8x8_basic.h"
#include "bttm.h"

#define tag "SSD1306"

// Defina o pino do botão
#define BUTTON_PIN GPIO_NUM_15

int power_state = 0;
int time_foco;
int time_inter;
int estado = 0;

void int_to_time_str(int minutes, int seconds, char* buffer) {
    buffer[0] = (minutes / 10) + '0';  // Primeiro dígito dos minutos
    buffer[1] = (minutes % 10) + '0';  // Segundo dígito dos minutos
    buffer[2] = ':';                   // Dois-pontos
    buffer[3] = (seconds / 10) + '0';  // Primeiro dígito dos segundos
    buffer[4] = (seconds % 10) + '0';  // Segundo dígito dos segundos
    buffer[5] = '\0';                  // Caractere nulo
}

void display(void *pvParameters)
{
    SSD1306_t dev;
    char timeStr[6];  // Buffer para "MM:SS\0"

    // Configuração inicial da tela OLED
    #if CONFIG_I2C_INTERFACE
    i2c_master_init(&dev, CONFIG_SDA_GPIO, CONFIG_SCL_GPIO, CONFIG_RESET_GPIO);
    #endif
    #if CONFIG_SPI_INTERFACE
    spi_master_init(&dev, CONFIG_MOSI_GPIO, CONFIG_SCLK_GPIO, CONFIG_CS_GPIO, CONFIG_DC_GPIO, CONFIG_RESET_GPIO);
    #endif

    #if CONFIG_FLIP
    dev._flip = true;
    #endif

    #if CONFIG_SSD1306_128x64
    ssd1306_init(&dev, 128, 64);
    #endif
    #if CONFIG_SSD1306_128x32
    ssd1306_init(&dev, 128, 32);
    #endif

    ssd1306_clear_screen(&dev, false);
    ssd1306_contrast(&dev, 0xff);

    // Configuração do pino do botão
    gpio_set_direction(BUTTON_PIN, GPIO_MODE_INPUT);
    gpio_set_pull_mode(BUTTON_PIN, GPIO_PULLUP_ONLY);
    bool button_state;
    int loop = 0; 
    bool last_state = 1;
    
    while (true)
    {
        // Verifica o estado do botão
        button_state = true;
        int state = 1; 
        if(loop == 0){
        button_state = gpio_get_level(BUTTON_PIN) == 0;  // Assume que o botão ativa o pino quando pressionado
        int state = 0; 
        }

        int seconds_foco = 1 * 10;  // 50 minutos convertidos em segundos
        int seconds_intervalo = 10 * 60;
        int x = 1;
        if(power_state == 1){
            if (button_state)
            {
                //button_state = !button_state;
                // Timer de 50 minutos
                while (seconds_foco > 0)
                {
                    int minutes = seconds_foco / 60;
                    int secs = seconds_foco % 60;
                    printf("Button state: %s\n", button_state == 1 ? "pressed" : "not pressed");
                    printf("Last state: %s\n", last_state == 1 ? "pressed" : "not pressed");
                    printf("State state: %d\n", state);
                    
                    int_to_time_str(minutes, secs, timeStr);

                    button_state = gpio_get_level(BUTTON_PIN) == 0;
                    if(button_state){
                        state++;
                        
                    }
                    if (state % 2 == 0)
                    {
                        if( x == 1){
                        ssd1306_clear_screen(&dev, false);
                        }
                        ssd1306_display_text(&dev, 0, "Pausado", 7, true);
                        ssd1306_display_text_x3(&dev, 3, timeStr, strlen(timeStr), true);
                        x++;
                        vTaskDelay(pdMS_TO_TICKS(1000)); // Atraso de 1 segundo
                        estado = 0;
                        time_foco = seconds_foco;
                        
                    }
                    else 
                    {
                        x = 1 ;
                        ssd1306_clear_screen(&dev, false);
                        ssd1306_display_text(&dev, 0, "Foco: ", 5, true);
                        ssd1306_display_text_x3(&dev, 3, timeStr, strlen(timeStr), true);

                        vTaskDelay(pdMS_TO_TICKS(1000)); // Atraso de 1 segundo
                        taskYIELD(); // Yield para permitir a execução de outras tarefas
                        seconds_foco--;
                        estado = 1; 
                        time_foco = seconds_foco;
                    }
                    if(power_state == 0){
                        estado = 0;
                        time_foco = 0; 
                        time_inter = 0;
                        break; 
                    }
                }

                // Timer de 10 minutos (600 segundos)
                while (seconds_intervalo > 0)
                {
                    int minutes = seconds_intervalo / 60;
                    int secs = seconds_intervalo % 60;

                    int_to_time_str(minutes, secs, timeStr);

                    button_state = gpio_get_level(BUTTON_PIN) == 0;
                    if(button_state){
                        state++;
                    }
                    if (state % 2 == 0)
                    {
                        if( x == 1){
                        ssd1306_clear_screen(&dev, false);
                        }
                        ssd1306_display_text(&dev, 0, "Pausado", 7, true);
                        ssd1306_display_text_x3(&dev, 3, timeStr, strlen(timeStr), true);
                        x++;
                        vTaskDelay(pdMS_TO_TICKS(1000)); // Atraso de 1 segundo
                        estado = 0;
                        time_inter = seconds_intervalo;
                        
                    }
                    else 
                    {
                        x = 1 ;
                        ssd1306_clear_screen(&dev, false);
                        ssd1306_display_text(&dev, 0, "Intervalo: ", 11, true);
                        ssd1306_display_text_x3(&dev, 3, timeStr, strlen(timeStr), true);

                        vTaskDelay(pdMS_TO_TICKS(1000)); // Atraso de 1 segundo
                        taskYIELD(); // Yield para permitir a execução de outras tarefas
                        seconds_intervalo--;
                        estado = 2;
                        time_inter = seconds_intervalo;
                    }
                    if(power_state == 0){
                        estado = 0;
                        time_foco = 0; 
                        time_inter = 0;
                        break; 
                    }
                }
                loop++;
            }
            else
            {
                ssd1306_clear_screen(&dev, false);
                ssd1306_display_text(&dev, 0, "Comecar?", 7, true);
                vTaskDelay(pdMS_TO_TICKS(1000)); // Atualiza a cada 1 segundo

                printf("Valor do Numero: %d", power_state);
            }}
        else{ 
             ssd1306_clear_screen(&dev, false);
        }
        
        vTaskDelay(pdMS_TO_TICKS(100)); // Adiciona um pequeno atraso para reduzir a carga da CPU
    }
}



int get_state(){
    return estado;
}

int get_time(){
    return time_foco;
}

int get_inter(){
    return time_inter;
}

int set_value(int state){
    power_state = state;
    printf("Entrou");
    return 1;
}