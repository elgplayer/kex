/* USER CODE BEGIN Header */
/**
  ******************************************************************************
  * @file           : main.h
  * @brief          : Header for main.c file.
  *                   This file contains the common defines of the application.
  ******************************************************************************
  * @attention
  *
  * Copyright (c) 2022 STMicroelectronics.
  * All rights reserved.
  *
  * This software is licensed under terms that can be found in the LICENSE file
  * in the root directory of this software component.
  * If no LICENSE file comes with this software, it is provided AS-IS.
  *
  ******************************************************************************
  */
/* USER CODE END Header */

/* Define to prevent recursive inclusion -------------------------------------*/
#ifndef __MAIN_H
#define __MAIN_H

#ifdef __cplusplus
extern "C" {
#endif

/* Includes ------------------------------------------------------------------*/
#include "stm32f0xx_hal.h"

/* Private includes ----------------------------------------------------------*/
/* USER CODE BEGIN Includes */

/* USER CODE END Includes */

/* Exported types ------------------------------------------------------------*/
/* USER CODE BEGIN ET */

/* USER CODE END ET */

/* Exported constants --------------------------------------------------------*/
/* USER CODE BEGIN EC */

/* USER CODE END EC */

/* Exported macro ------------------------------------------------------------*/
/* USER CODE BEGIN EM */

/* USER CODE END EM */

/* Exported functions prototypes ---------------------------------------------*/
void Error_Handler(void);

/* USER CODE BEGIN EFP */

/* USER CODE END EFP */

/* Private defines -----------------------------------------------------------*/
#define brake_light_Pin GPIO_PIN_0
#define brake_light_GPIO_Port GPIOA
#define assi_yellow_rear_Pin GPIO_PIN_1
#define assi_yellow_rear_GPIO_Port GPIOA
#define assi_blue_rear_Pin GPIO_PIN_2
#define assi_blue_rear_GPIO_Port GPIOA
#define blue_LED_Pin GPIO_PIN_9
#define blue_LED_GPIO_Port GPIOC
#define yellow_LED_Pin GPIO_PIN_8
#define yellow_LED_GPIO_Port GPIOA
#define green_LED_Pin GPIO_PIN_9
#define green_LED_GPIO_Port GPIOA
#define buzzern_Pin GPIO_PIN_10
#define buzzern_GPIO_Port GPIOA
#define ts_off_Pin GPIO_PIN_2
#define ts_off_GPIO_Port GPIOD
#define close_airs_Pin GPIO_PIN_3
#define close_airs_GPIO_Port GPIOB
#define reset_Pin GPIO_PIN_4
#define reset_GPIO_Port GPIOB

/* USER CODE BEGIN Private defines */

/* USER CODE END Private defines */

#ifdef __cplusplus
}
#endif

#endif /* __MAIN_H */
