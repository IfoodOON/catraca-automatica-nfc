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
bool ultimoEstadoSensor = false;

unsigned long tempoSaida = 0;

void setup() {

  Serial.begin(9600);

  pinMode(sensor, INPUT_PULLUP);
  pinMode(rele, OUTPUT);

  cancela.attach(servoPin);

  // Estado inicial
  cancela.write(175);      // Cancela fechada
  digitalWrite(rele, HIGH); // LED apagado
}

void loop() {

  // HIGH = carro detectado
  // LOW = sem carro
  bool carro = (digitalRead(sensor) == HIGH);

  //====================================
  // AVISA O PYTHON QUANDO O SENSOR MUDA
  //====================================
  if (carro != ultimoEstadoSensor) {

    if (carro) {

      Serial.println("CARRO");

      // Acende LED indicando veículo aguardando
      digitalWrite(rele, LOW);

    } else {

      Serial.println("SEM_CARRO");

      // Se a cancela estiver fechada apaga o LED
      if (!aberta) {
        digitalWrite(rele, HIGH);
      }
    }

    ultimoEstadoSensor = carro;
  }

  //====================================
  // RECEBE COMANDOS DO PYTHON
  //====================================
  if (Serial.available()) {

    String comando = Serial.readStringUntil('\n');
    comando.trim();

    if (comando == "ABRIR" && !aberta) {

      Serial.println("ABERTA");

      // Levanta rapidamente
      cancela.write(90);

      // Mantém LED ligado
      digitalWrite(rele, LOW);

      aberta = true;
      aguardandoFechar = false;
    }

  }

  //====================================
  // CONTROLE DE FECHAMENTO
  //====================================
  if (aberta) {

    // Carro saiu do sensor
    if (!carro && !aguardandoFechar) {

      tempoSaida = millis();
      aguardandoFechar = true;

    }

    // Outro carro entrou, cancela o fechamento
    if (carro) {

      aguardandoFechar = false;

    }

    // Espera 3 segundos antes de fechar
    if (aguardandoFechar && millis() - tempoSaida >= 3000) {

      // Fecha lentamente
      for (int angulo = 90; angulo <= 175; angulo++) {

        cancela.write(angulo);
        delay(20);

      }

      aberta = false;
      aguardandoFechar = false;

      // Apaga LED
      digitalWrite(rele, HIGH);

      Serial.println("FECHADA");
    }
  }
}
