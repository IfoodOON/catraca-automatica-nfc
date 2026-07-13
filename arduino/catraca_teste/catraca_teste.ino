#include <Servo.h>

// =============================
// Definição dos pinos
// =============================
const int sensor = 2;      // Sensor de proximidade
const int rele = 3;        // Relé (ou LED)
const int servoPin = 9;    // Servo da cancela

Servo cancela;

// Variáveis de controle
bool aberta = false;
bool aguardandoFechar = false;
unsigned long tempoSaida = 0;

void setup() {

  Serial.begin(9600);

  pinMode(sensor, INPUT_PULLUP);
  pinMode(rele, OUTPUT);

  cancela.attach(servoPin);

  // Estado inicial
  cancela.write(175);       // Cancela fechada
  digitalWrite(rele, HIGH); // LED apagado

  Serial.println("Sistema iniciado.");
}

void loop() {

  // HIGH = carro detectado
  // LOW = sem carro
  bool carro = (digitalRead(sensor) == HIGH);

  // =============================
  // CARRO CHEGOU
  // =============================
  if (carro && !aberta) {

    Serial.println("Carro detectado.");

    // Acende LED
    digitalWrite(rele, LOW);

    // Abre a cancela
    cancela.write(90);

    aberta = true;
    aguardandoFechar = false;
  }

  // =============================
  // CARRO SAIU
  // =============================
  if (aberta) {

    // Quando o carro sair
    if (!carro && !aguardandoFechar) {

      Serial.println("Carro saiu. Aguardando 3 segundos...");

      tempoSaida = millis();
      aguardandoFechar = true;
    }

    // Se o carro voltou, cancela o fechamento
    if (carro) {
      aguardandoFechar = false;
    }

    // Fecha após 3 segundos
    if (aguardandoFechar && millis() - tempoSaida >= 3000) {

      Serial.println("Fechando cancela...");

      // Fecha lentamente
      for (int angulo = 90; angulo <= 175; angulo++) {

        cancela.write(angulo);
        delay(20);

      }

      // Apaga LED
      digitalWrite(rele, HIGH);

      aberta = false;
      aguardandoFechar = false;

      Serial.println("Cancela fechada.");
    }
  }
}
