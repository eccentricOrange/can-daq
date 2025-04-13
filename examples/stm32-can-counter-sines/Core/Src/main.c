#include "stm32f4xx.h"
#include <math.h>

#define PI acos(-1.0)

// sine constants
#define AMPLITUDE 127.0
#define FREQUENCY 5  // Hz
#define SAMPLING_FREQUENCY 3789  // Hz. this weird value gives us real 1 kHz

// CAN constants
#define DLC 8
#define CAN_ID 0x123

uint8_t data[DLC];
int16_t value;

uint32_t id = 0;

void configure_LEDs() {
    // LEDs on D port: 12, 13, 14, 15

    // enable GPIO D clock
    RCC->AHB1ENR |= 0b1UL << 3;

    // set the pins as output
    GPIOD->MODER &= ~(0b11111111 << (12 * 2));  // reset the modes
    GPIOD->MODER |= 0b01010101 << (12 * 2);  // set as outputs

    // set the clock for TIM2
    RCC->APB1ENR |= 0b1UL;
}

void delay_microseconds(uint16_t us)
{
    TIM2->PSC = 16-1; //16 MHz / 16 = 1 MHz (1 us)
    TIM2->ARR = us-1;   // desired delay

    TIM2->CR1 |= TIM_CR1_CEN;
    while(!(TIM2->SR & TIM_SR_UIF)){} //wait UIF to be set

    TIM2->SR &= ~TIM_SR_UIF; //reset UIF

    TIM2->CR1 &= ~TIM_CR1_CEN; // Disable the timer
}


void configure_CAN() {
	/* Configure CAN for 1 Mbps */


    // enable GPIO B clock
    RCC->AHB1ENR |= 0b1UL << 1;

    // set pin modes for CAN
    // PB8: CAN RX
    // PB9: CAN TX
    GPIOB->MODER &= ~(0b1111 << (2 * 8));  // clear mode register
    GPIOB->MODER |= 0b1010 << (2 * 8);  // set to AFR
    GPIOB->AFR[1] &= ~(0b1111 | (0b1111 << 4));  // clear the AFR
    GPIOB->AFR[1] |= 9 | (9 << 4);  // set the AFR to AF 9

    // enable the CAN clock
    RCC->APB1ENR |= 0b1 << 25;

    // Enter Initialization mode
    CAN1->MCR |= (0b1 << 0);  // set INRQ bit
    while(!(CAN1->MSR & 0b1));   // Wait until INAK bit is set

    // Exit Sleep Mode
    CAN1->MCR &= ~(0b1<<1);  // clear INRQ bit
    while(CAN1->MSR & 0b10);  // Wait for SLAK bit to clear

    // CAN Baudrate configuration
    CAN1->BTR &= ~(0b11<<24);  // SWJ 1 Time Quantum
    CAN1->BTR &= ~((0b1111 << 16) | (0b111 << 20));  // reset both segments to 1
    CAN1->BTR |= ((13-1) << 16);  // Time Segment 1
    CAN1->BTR |= ((2-1) << 20);   // Time Segment 2
    CAN1->BTR |= ((1-1) << 0);    // Baud-Rate Prescaler

    // Exit Initialization mode
    CAN1->MCR &= ~(1<<0);
    while(CAN1->MSR & 0b1);

    // Filter Configuration
    CAN1->FMR |= 1<<0;   // Enter filter initialization mode
    CAN1->FMR |= 14<<8;  // Set start bank for CAN2
    CAN1->FS1R |= 1<<13; // 32-bit scale configuration for filter
    CAN1->FM1R |= (1<<13);   // Identifier List Mode
    CAN1->sFilterRegister[13].FR1 = 0x150 << 21; // Filter STD ID: 0x123
    CAN1->FA1R |= (1<<13); // Enable filter 13
    CAN1->FMR &= ~(1<<0);  // Exit filter initialization mode
}

void CAN_Tx(uint8_t* data, uint32_t count) {
    // Set up CAN identifier (Standard ID = 0x123)
    CAN1->sTxMailBox[0].TIR = 0;              // Clear TIR
    CAN1->sTxMailBox[0].TIR |= (CAN_ID << 21); // Set STD ID to 0x150

    // Set DLC (8 bytes of data)
    CAN1->sTxMailBox[0].TDTR = DLC;  // DLC = 8

    // Set Data payload (8 bytes)
    CAN1->sTxMailBox[0].TDLR = count;
    CAN1->sTxMailBox[0].TDHR = (data[7] << 24) | (data[6] << 16) | (data[5] << 8) | data[4];

    // Request for transmission
    CAN1->sTxMailBox[0].TIR |= 1;
}

int main(void) {
    configure_LEDs();
    configure_CAN();
    float theta;

    float phase_shifts[4];

    for (int i = 0; i < 4; ++i) {
		phase_shifts[i] = (i * PI / 2.0);
	}

    // set up an infinite while loop
    // within the loop, keep generating a sine wave with the given frequency and amplitude
    // at every time interval defined by the sampling frequency, send the data over CAN
    // also toggle the LEDs at every time interval
    for (int count = 0; count < 85; ++count) {

    	for (int i = 0; i < SAMPLING_FREQUENCY / FREQUENCY; i++) {
    		theta = 2.0 * PI * FREQUENCY * i / SAMPLING_FREQUENCY;

    		for (int j = 0; j < 4; j++) {
    			data[j+4] = (uint8_t) (AMPLITUDE + (int16_t) (AMPLITUDE * sin(theta + phase_shifts[j])));
    		}

    		CAN_Tx(data, id);
    		GPIOD->ODR ^= 0b1111 << 12;
    		delay_microseconds(1e6 / SAMPLING_FREQUENCY);
			id++;

    	}
    }

    GPIOD->ODR &= ~(0b1111 << 12);

    while(1) {};
}
