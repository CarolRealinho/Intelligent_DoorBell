#include <rgb_lcd.h> // Inclui a biblioteca para usar o display LCD RGB
#include "pitches.h" // Inclui a biblioteca de notas musicais para o uso do buzzer
#define PINO_BUZZER 9 // Define o pino do Arduino conectado ao buzzer como pino 9
#define PINO_BOTAO 2 // Define o pino do Arduino conectado ao botão como pino 2
#define INTERVALO 300000 // Define o intervalo de tempo em milissegundos (5 minutos = 300000 ms)

int melodia0[] = {660, 550, 440}; // Define a melodia 0 como um array de frequências
int DuracaoNotas0[] = {700, 700, 700}; // Define a duração das notas da melodia 0 em milissegundos

int melodia1[] = {660, 770, 880}; // Define a melodia 1 como um array de frequências
int DuracaoNotas1[] = {700, 700, 700}; // Define a duração das notas da melodia 1 em milissegundos

int melodia2[] = {440, 494, 523, 587}; // Define a melodia 2 como um array de frequências
int DuracaoNotas2[] = {500, 250, 250, 500}; // Define a duração das notas da melodia 2 em milissegundos

rgb_lcd lcd; // Cria um objeto da classe rgb_lcd para manipular o display LCD RGB

int EstadoBotao = 0; // Variável para armazenar o estado atual do botão
int ultimoEstadoBotao = 0; // Variável para armazenar o último estado do botão
unsigned long ultimoEstadoDebounce = 0; // Variável para armazenar o último momento em que o botão foi acionado
unsigned long debounceDelay = 50; // Tempo de debounce para evitar leituras instáveis do botão
int ContadorBotao = -1; // Variável para contar o número de vezes que o botão foi pressionado
int escolhaToque; // Variável para armazenar a escolha do toque
String mensagem; // Variável para armazenar uma mensagem
String mensagem_lcd; // Variável para armazenar uma mensagem para exibir no LCD

// Variáveis para medir o tempo
unsigned long ms_anterior = 0; // armazena o tempo (em ms) desde que uma função foi executada pela última vez
unsigned long ms_atual; // Variável para armazenar o tempo atual

void setup() {
  Serial.begin(9600); // Inicializa a comunicação serial com uma taxa de transmissão de 9600 bps
  lcd.begin(16, 2); // Inicializa o LCD com 16 colunas e 2 linhas
  pinMode(PINO_BUZZER, OUTPUT); // Define o pino do buzzer como saída
  pinMode(PINO_BOTAO, INPUT_PULLUP); // Define o pino do botão como entrada com pull-up interno ativado
}

void imprimirMensagem(String mensagem) {
  
  /**
 * Função para exibir uma mensagem no LCD.
 *
 * param mensagem: A mensagem a ser exibida no LCD
 */

  int tamanho_mensagem = mensagem.length(); // Calcula o comprimento da mensagem

  if (tamanho_mensagem > 16 && tamanho_mensagem <= 32) { // Verifica se a mensagem tem entre 17 e 32 caracteres
    lcd.setCursor(0, 0); // Define o cursor para a primeira linha do LCD
    lcd.print(mensagem.substring(0, 16)); // Imprime os primeiros 16 caracteres da mensagem na primeira linha do LCD
    lcd.setCursor(0, 1); // Define o cursor para a segunda linha do LCD
    lcd.print(mensagem.substring(16)); // Imprime os caracteres restantes da mensagem na segunda linha do LCD
    delay(10000); // Aguarda 10 segundos
    lcd.clear(); // Limpa o LCD após o tempo de exibição
  } 
  else if (tamanho_mensagem > 32) { // Se a mensagem tem mais de 32 caracteres
    lcd.setCursor(0, 0); // Define o cursor para a primeira linha do LCD
    lcd.print(mensagem.substring(0, 16)); // Imprime os primeiros 16 caracteres da mensagem na primeira linha do LCD
    delay(1500); // Aguarda 1.5 segundos
    lcd.clear(); // Limpa o LCD
    for (int i = 0; i < tamanho_mensagem - 16; i++) { // Loop para rodar a mensagem na primeira linha do LCD
      lcd.setCursor(0, 0);  // Define o cursor para a primeira linha do LCD
      lcd.print(mensagem.substring(i, 16 + i)); // Imprime um segmento deslocado da mensagem na primeira linha do LCD
      delay(400); // Aguarda 0.4 segundos
      lcd.clear(); // Limpa o LCD
    }
    lcd.setCursor(0, 0); // Define o cursor para a primeira linha do LCD
    lcd.print(mensagem.substring(tamanho_mensagem - 16)); // Imprime os últimos 16 caracteres da mensagem na primeira linha do LCD
    delay(3000); // Aguarda 3 segundos
    lcd.clear(); // Limpa o LCD
  } 
  else { // Se a mensagem tem 16 ou menos caracteres
    lcd.setCursor(0, 0); // Define o cursor para a primeira linha do LCD
    lcd.print(mensagem); // Imprime a mensagem na primeira linha do LCD
    delay(3000); // Aguarda 3 segundos
    lcd.clear(); // Limpa o LCD
  }
}

void tocarMelodia(int escolha) {

  /**
  * Função para tocar uma melodia no buzzer.
  * 
  * param escolha: A escolha da melodia (1, 2 ou 3).
  */

  int* melody; // Ponteiro para a melodia selecionada
  int* noteDurations; // Ponteiro para as durações das notas da melodia selecionada
  int notes; // Número de notas na melodia selecionada

  // Determinar qual melodia tocar com base na escolha
  switch (escolha) {
    case 1: // Se a escolha for 1
      melody = melodia0; // Atribui o array de notas da melodia 0 ao ponteiro de melodia
      noteDurations = DuracaoNotas0; // Atribui o array de durações das notas da melodia 0 ao ponteiro de durações
      notes = sizeof(melodia0) / sizeof(int); // Calcula o número de notas na melodia 0
      break;
    case 2: // Se a escolha for 2
      melody = melodia1; // Atribui o array de notas da melodia 1 ao ponteiro de melodia
      noteDurations = DuracaoNotas1; // Atribui o array de durações das notas da melodia 1 ao ponteiro de durações
      notes = sizeof(melodia1) / sizeof(int); // Calcula o número de notas na melodia 1
      break;
    case 3: // Se a escolha for 3
      melody = melodia2; // Atribui o array de notas da melodia 2 ao ponteiro de melodia
      noteDurations = DuracaoNotas2; // Atribui o array de durações das notas da melodia 2 ao ponteiro de durações
      notes = sizeof(melodia2) / sizeof(int); // Calcula o número de notas na melodia 2
      break;
    default:
      return; // Escolha inválida, não faz nada
  }

  // Toca a melodia
  for (int i = 0; i < notes; i++) { // Loop sobre todas as notas na melodia
    tone(PINO_BUZZER, melody[i]); // Toca a nota
    delay(noteDurations[i]); // Aguarda a duração da nota
    noTone(PINO_BUZZER); // Para de tocar a nota
    delay(50); // Pequeno atraso entre as notas
  }
}


void loop() {
  
  // Inicialização
  if (Serial.available() > 0) { // Verifica se há dados disponíveis na porta serial
    mensagem = Serial.readString(); // Lê a mensagem enviada do Python

    if (mensagem.charAt(0) == '/') { // Verifica se o primeiro caractere da mensagem é '/'
      // Caractere especial indica uma mensagem do toque selecionado
      escolhaToque = mensagem.charAt(1) - '0'; // Extrai a escolha do toque
      tocarMelodia(escolhaToque); // Toca a melodia selecionada
    } else {
      // Exibe a mensagem no LCD
      mensagem_lcd = mensagem; // Atribui a mensagem ao LCD
      imprimirMensagem(mensagem_lcd); // Exibe a mensagem no LCD
      lcd.clear(); // Limpa o LCD
    }
  }

  // Reset do tempo
  ms_atual = millis(); // Obtém o tempo atual em milissegundos desde o início do programa
  if(ms_atual - ms_anterior >= INTERVALO){ // Verifica se passou o intervalo de tempo definido
    ContadorBotao = 0; // Faz reset ao contador do botão
    ms_anterior = ms_atual; // Atualiza o tempo anterior para o tempo atual
  }
  
  // Campainha
  int reading = digitalRead(PINO_BOTAO); // Lê o estado atual do botão
  if (reading != ultimoEstadoBotao) { // Verifica se houve mudança de estado do botão
    ultimoEstadoDebounce = millis(); // Atualiza o tempo de debounce
  }
  if ((millis() - ultimoEstadoDebounce) > debounceDelay) { // Verifica se o tempo de debounce passou
    if (reading != EstadoBotao) { // Verifica se o estado atual do botão é diferente do estado anterior
      EstadoBotao = reading; // Atualiza o estado do botão
      if (EstadoBotao == HIGH) { // Verifica se o botão foi pressionado
        ContadorBotao++; // Incrementa o contador do botão
        if (ContadorBotao == 1) { // Se o botão foi pressionado uma vez
          Serial.println("1"); // Envia "1" para o terminal Python
        } else if (ContadorBotao == 3) { // Se o botão foi pressionado três vezes
        Serial.println("3"); // Envia "3" para o terminal Python
        } else if (ContadorBotao >= 5) { // Se o botão foi pressionado cinco vezes ou mais
         Serial.println("5"); // Envia "SPAM" para o terminal Python
        }
        tocarMelodia(escolhaToque); // Toca a melodia selecionada
        imprimirMensagem(mensagem_lcd); // Exibe a mensagem no LCD
      }
    }
  }
  ultimoEstadoBotao = reading; // Atualiza o último estado do botão
}
