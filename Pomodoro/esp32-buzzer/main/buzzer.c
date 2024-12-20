#include <stdio.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "driver/gpio.h"
#include "esp_rom_sys.h"
#include "mqtt.h"
#include "buzzer.h"

#define BUZZER_PIN 4 // Definir o pino GPIO para o buzzer
// Frequências das notas musicais (em Hz)
#define NOTE_B0  31
#define NOTE_C1  33
#define NOTE_CS1 35
#define NOTE_D1  37
#define NOTE_DS1 39
#define NOTE_E1  41
#define NOTE_F1  44
#define NOTE_FS1 46
#define NOTE_G1  49
#define NOTE_GS1 52
#define NOTE_A1  55
#define NOTE_AS1 58
#define NOTE_B1  62
#define NOTE_C2  65
#define NOTE_CS2 69
#define NOTE_D2  73
#define NOTE_DS2 78
#define NOTE_E2  82
#define NOTE_F2  87
#define NOTE_FS2 93
#define NOTE_G2  98
#define NOTE_GS2 104
#define NOTE_A2  110
#define NOTE_AS2 117
#define NOTE_B2  123
#define NOTE_C3  131
#define NOTE_CS3 139
#define NOTE_D3  147
#define NOTE_DS3 156
#define NOTE_E3  165
#define NOTE_F3  175
#define NOTE_FS3 185
#define NOTE_G3  196
#define NOTE_GS3 208
#define NOTE_A3  220
#define NOTE_AS3 233
#define NOTE_B3  247
#define NOTE_C4  261
#define NOTE_CS4 277
#define NOTE_D4  294
#define NOTE_DS4 311
#define NOTE_E4  329
#define NOTE_F4  349
#define NOTE_FS4 370
#define NOTE_G4  392
#define NOTE_GS4 415
#define NOTE_A4  440
#define NOTE_AS4 466
#define NOTE_B4  494
#define NOTE_C5  523
#define NOTE_CS5 554
#define NOTE_D5  587
#define NOTE_DS5 622
#define NOTE_E5  659
#define NOTE_F5  698
#define NOTE_FS5 740
#define NOTE_G5  784
#define NOTE_GS5 831
#define NOTE_A5  880
#define NOTE_AS5 932
#define NOTE_B5  988
#define NOTE_C6  1047
#define NOTE_CS6 1109
#define NOTE_D6  1175
#define NOTE_DS6 1245
#define NOTE_E6  1319
#define NOTE_F6  1397
#define NOTE_FS6 1480
#define NOTE_G6  1568
#define NOTE_GS6 1661
#define NOTE_A6  1760
#define NOTE_AS6 1865
#define NOTE_B6  1976
#define NOTE_C7  2093
#define NOTE_CS7 2217
#define NOTE_D7  2349
#define NOTE_DS7 2489
#define NOTE_E7  2637
#define NOTE_F7  2794
#define NOTE_FS7 2960
#define NOTE_G7  3136
#define NOTE_GS7 3322
#define NOTE_A7  3520
#define NOTE_AS7 3729
#define NOTE_B7  3951
#define NOTE_C8  4186
#define NOTE_CS8 4435
#define NOTE_D8  4699
#define NOTE_DS8 4978

// Função para inicializar o pino do buzzer
void buzzer_init(void)
{
    gpio_reset_pin(BUZZER_PIN);
    gpio_set_direction(BUZZER_PIN, GPIO_MODE_OUTPUT);
}

// Função para tocar uma nota
void play_note(int frequency, int duration_ms)
{
    int period = 1000000 / frequency; // Período em microsegundos
    int half_period = period / 2; // Meio período
    int cycles = (duration_ms * 1000) / period; // Número de ciclos

    // Enviar estado do buzzer "ligado" e a frequência atual para o Thingsboard
    char mensagem[100];
    sprintf(mensagem, "{\"buzzer_status\": \"ligado\", \"frequencia\": %d}", frequency);
    mqtt_envia_mensagem(client, "v1/devices/me/telemetry", mensagem);

    for (int i = 0; i < cycles; i++)
    {
        gpio_set_level(BUZZER_PIN, 1);
        esp_rom_delay_us(half_period); // ESP-IDF delay function
        gpio_set_level(BUZZER_PIN, 0);
        esp_rom_delay_us(half_period);
    }

    // Após tocar a nota, enviar estado "desligado"
    sprintf(mensagem, "{\"buzzer_status\": \"desligado\"}");
    mqtt_envia_mensagem(client, "v1/devices/me/telemetry", mensagem);
}

// Função para tocar a melodia de Star Wars
void play_star_wars_theme(void)
{
    int melody[] = {
        NOTE_A4, NOTE_A4, NOTE_F4, NOTE_C5, NOTE_A4, NOTE_F4, NOTE_C5, NOTE_A4,
        NOTE_E5, NOTE_E5, NOTE_E5, NOTE_F5, NOTE_C5, NOTE_GS4, NOTE_F4, NOTE_C5, NOTE_A4,
        NOTE_A5, NOTE_A4, NOTE_A4, NOTE_A5, NOTE_GS5, NOTE_G5, NOTE_FS5, NOTE_F5, NOTE_FS5,
        NOTE_AS4, NOTE_DS5, NOTE_D5, NOTE_CS5, NOTE_C5, NOTE_B4, NOTE_C5,
        NOTE_F4, NOTE_GS4, NOTE_F4, NOTE_A4, NOTE_C5, NOTE_A4, NOTE_C5, NOTE_E5,
        NOTE_A5, NOTE_A4, NOTE_A4, NOTE_A5, NOTE_GS5, NOTE_G5, NOTE_FS5, NOTE_F5, NOTE_FS5,
        NOTE_AS4, NOTE_DS5, NOTE_D5, NOTE_CS5, NOTE_C5, NOTE_B4, NOTE_C5,
        NOTE_F4, NOTE_GS4, NOTE_F4, NOTE_C5, NOTE_A4, NOTE_F4, NOTE_C5, NOTE_A4
    };
    int noteDurations[] = {
        500, 500, 350, 150, 500, 350, 150, 1000,
        500, 500, 500, 350, 150, 500, 350, 150, 1000,
        500, 350, 150, 500, 250, 250, 125, 125, 250,
        250, 500, 250, 250, 125, 125, 250,
        250, 500, 250, 250, 125, 125, 250, 250,
        500, 350, 150, 500, 250, 250, 125, 125, 250,
        250, 500, 250, 250, 125, 125, 250,
        250, 500, 250, 250, 125, 125, 250, 250
    };

    int num_notes = sizeof(melody) / sizeof(melody[0]);
    for (int i = 0; i < num_notes; i++)
    {
        play_note(melody[i], noteDurations[i]);
        vTaskDelay(100 / portTICK_PERIOD_MS); // Pequena pausa entre as notas
    }
}

void play_timer_buzzer(void)
{
    int buzzer_note = NOTE_DS8; // Nota da campainha
    int buzzer_duration = 1000; // Duração de cada toque em milissegundos
    int total_duration = 5000; // Duração total de 5 segundos

    int elapsed_time = 0;
    while (elapsed_time < total_duration)
    {
        play_note(buzzer_note, buzzer_duration);
        vTaskDelay(100 / portTICK_PERIOD_MS); // Pequena pausa após tocar a nota
        elapsed_time += buzzer_duration + 100;
    }
}
