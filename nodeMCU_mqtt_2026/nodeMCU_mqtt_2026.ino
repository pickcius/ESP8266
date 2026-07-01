#include <ESP8266WiFi.h>
#include <PubSubClient.h>

// WiFi settings
const char *ssid = "RAU-IOT";             
const char *password = "10Tr4uEnsino";

// MQTT Broker settings
const char *mqtt_broker = "broker.emqx.io";  // EMQX broker endpoint
const char *mqtt_topic_envio = "topicEdilson_ifsc/3";     // Tópico para envio de dados (A0)
const char *mqtt_topic_comando = "topicEdilson_ifsc/ledClaudio"; // NOVO: Tópico que o Django enviará comandos

const char *mqtt_username = "emqx";  // MQTT username for authentication
const char *mqtt_password = "public";  // MQTT password for authentication
const int mqtt_port = 1883;  // MQTT port (TCP)

WiFiClient espClient;
PubSubClient mqtt_client(espClient);

// Controle de tempo não-bloqueante (substitutos do delay)
unsigned long lastMsgTime = 0;
const unsigned long interval = 5000; // 5 segundos

// Definição do LED interno do NodeMCU
const int ledPin = LED_BUILTIN; 

void connectToWiFi();
void connectToMQTTBroker();
void mqttCallback(char *topic, byte *payload, unsigned int length);

void setup() {
    Serial.begin(115200);
    
    // Configura o pino do LED como saída
    pinMode(ledPin, OUTPUT);
    digitalWrite(ledPin, HIGH); // No NodeMCU, HIGH desliga o LED interno (lógica invertida)

    connectToWiFi();
    mqtt_client.setServer(mqtt_broker, mqtt_port);
    mqtt_client.setCallback(mqttCallback);
    connectToMQTTBroker();
}

void connectToWiFi() {
    WiFi.begin(ssid, password);
    Serial.print("Conectando ao WiFi");
    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print(".");
    }
    Serial.println("\nConectado a rede WiFi");
}

void connectToMQTTBroker() {
    while (!mqtt_client.connected()) {
        String client_id = "esp8266-client-" + String(WiFi.macAddress());
        Serial.printf("Conectando ao MQTT Broker %s.....\n", client_id.c_str());
        if (mqtt_client.connect(client_id.c_str(), mqtt_username, mqtt_password)) {
            Serial.println("Conectado ao MQTT broker");
            
            // Inscreve-se no tópico de comando para ouvir o Django
            mqtt_client.subscribe(mqtt_topic_comando);
            
            // Publica mensagem inicial
            mqtt_client.publish(mqtt_topic_envio, "Ola EMQX sou ESP8266 ^^");
        } else {
            Serial.print("Falha ao conectar no MQTT broker, rc=");
            Serial.print(mqtt_client.state());
            Serial.println(" tentando novamente em 5 segundos");
            delay(5000);
        }
    }
}

// Esta função é chamada automaticamente sempre que uma mensagem chega nos tópicos inscritos
void mqttCallback(char *topic, byte *payload, unsigned int length) {
    Serial.print("Mensagem recebida do tópico: ");
    Serial.println(topic);
    
    // Converte o payload para uma String para facilitar a manipulação
    String message;
    for (unsigned int i = 0; i < length; i++) {
        message += (char)payload[i];
    }
    
    Serial.print("Conteúdo da mensagem: ");
    Serial.println(message);
    Serial.println("-----------------------");

    // Verifica se a mensagem veio do tópico do LED
    if (String(topic) == mqtt_topic_comando) {
        // OBSERVAÇÃO: O LED_BUILTIN do NodeMCU acende com LOW e apaga com HIGH
        if (message == "on") {
            digitalWrite(ledPin, LOW);  // Liga o LED
            Serial.println("LED LIGADO");
        } 
        else if (message == "off") {
            digitalWrite(ledPin, HIGH); // Desliga o LED
            Serial.println("LED DESLIGADO");
        }
    }
}

void publish_sensor_data(int id, float temp) {
    String topic = "sensor/" + String(id);
    mqtt_client.publish(topic.c_str(), String(temp).c_str());
}

void loop() {
    if (!mqtt_client.connected()) {
        connectToMQTTBroker();
    }
    
    // Essencial para manter a comunicação ativa e processar o callback de entrada
    mqtt_client.loop();

    // Envia a temperatura a cada 5 segundos sem travar o código
    unsigned long now = millis();
    if (now - lastMsgTime > interval) {
        lastMsgTime = now;

        int temperatura = analogRead(A0);
        String payload = String(temperatura);
        
        // Publica no tópico de envio
        mqtt_client.publish(mqtt_topic_envio, payload.c_str());
        Serial.printf("Temperatura enviada: %s\n", payload.c_str());
    }
}
