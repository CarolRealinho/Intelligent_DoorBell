#include <WebServer.h> // Inclui a biblioteca WebServer para criar um servidor web no ESP32
#include <WiFi.h> // Inclui a biblioteca WiFi para configurar a conexão Wi-Fi no ESP32
#include <esp32cam.h> // Inclui a biblioteca esp32cam para controlar a câmera OV2640 integrada ao ESP32
 
const char* WIFI_SSID = "OPPO Reno6 5G"; // Define o nome da rede Wi-Fi a que a camera está conectada
const char* WIFI_PASS = "y3aiasss"; // Define a palavra-passe da rede Wi-Fi a que a camera está conectada
 
WebServer server(80); // Cria um objeto de servidor web na porta 80

static auto hiRes = esp32cam::Resolution::find(800, 600); // Define a resolução da captura de imagem como 800x600 pixels

void serveJpg()
{

  /**
  * Função que captura uma imagem da câmera e a serve como um arquivo JPEG.
  * Se a captura falhar, retorna um código de status 503.
  */

  auto frame = esp32cam::capture(); // Captura um frame da câmera OV2640
  if (frame == nullptr) {
    Serial.println("CAPTURE FAIL"); // Imprime uma mensagem de erro se a captura falhar
    server.send(503, "", ""); // Envia um código de status 503 (Serviço Indisponível) para o cliente
    return;
  }
  Serial.printf("CAPTURE OK %dx%d %db\n", frame->getWidth(), frame->getHeight(),
                static_cast<int>(frame->size())); // Imprime informações sobre o frame capturado
 
  server.setContentLength(frame->size()); // Define o tamanho do conteúdo como o tamanho do frame capturado 
  server.send(200, "image/jpeg"); // Envia um código de status 200 (OK) com o tipo de conteúdo "image/jpeg" para o cliente
  WiFiClient client = server.client(); // Cria um cliente WiFi para enviar o quadro capturado
  frame->writeTo(client); // Escreve o quadro capturado no cliente WiFi para ser enviado ao cliente HTTP
}
 
 
void handleJpgHi()
{

  /**
  * Função que configura a resolução da câmera para alta resolução e serve uma imagem JPEG.
  */

  if (!esp32cam::Camera.changeResolution(hiRes)) {
    Serial.println("SET-HI-RES FAIL"); // Imprime uma mensagem de erro se não for possível alterar a resolução para a resolução hiRes
  }
  serveJpg(); // Chama a função serveJpg() para capturar e servir uma imagem em alta resolução
}
 
 
void  setup(){

  /**
  * Função que configura e inicializa a câmera e a conexão Wi-Fi.
  */

  Serial.begin(115200); // Inicializa a comunicação serial com uma taxa de transmissão de 115200 bps
  Serial.println(); // Imprime uma nova linha na comunicação serial

  // Configuração da câmera
  {
    using namespace esp32cam;
    Config cfg; // Cria um objeto de configuração da câmera
    cfg.setPins(pins::AiThinker); // Define os pinos da câmera como os pinos padrão da placa Ai-Thinker
    cfg.setResolution(hiRes); // Define a resolução da câmera como a resolução hiRes
    cfg.setBufferCount(2); // Define o número de buffers de captura como 2
    cfg.setJpeg(80); // Define a qualidade JPEG como 80%
 
    bool ok = Camera.begin(cfg); // Inicializa a câmera com as configurações especificadas
    Serial.println(ok ? "CAMERA OK" : "CAMERA FAIL"); // Imprime se a inicialização da câmera foi bem-sucedida ou não
  }

  // Configuração da conexão Wi-Fi
  WiFi.persistent(false); // Desabilita a persistência das configurações Wi-Fi para economizar memória
  WiFi.mode(WIFI_STA); // Configura o modo de operação Wi-Fi como estação (cliente)
  WiFi.begin(WIFI_SSID, WIFI_PASS); // Conecta-se à rede Wi-Fi especificada com o SSID e a senha fornecidos
  
  // Aguarda a conexão Wi-Fi ser estabelecida
  while (WiFi.status() != WL_CONNECTED) {
    delay(500); // Aguarda 500 milissegundos antes de verificar novamente o status da conexão Wi-Fi
  }

  // Imprime o endereço IP local
  Serial.print("http://");
  Serial.println(WiFi.localIP()); // Imprime o endereço IP local atribuído ao ESP32-CAM
  Serial.println("  /cam-hi.jpg"); // Imprime a URL para acessar a imagem em alta resolução
 
  // Define a função de tratamento para a rota "/cam-hi.jpg"
  server.on("/cam-hi.jpg", handleJpgHi);
  
  // Inicia o servidor web
  server.begin();
}
 
void loop()
{

  /**
  * Função que manipula as requisições dos clientes para o servidor web.
  */

  server.handleClient(); // Manipula as requisições dos clientes para o servidor web
}