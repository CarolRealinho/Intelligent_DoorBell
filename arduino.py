from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QPushButton, QVBoxLayout, QWidget, QLineEdit, QComboBox,  QMessageBox
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QFileDialog
from PyQt5.QtCore import QUrl, Qt, QThread
from PyQt5.QtGui import QIcon
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import os
import serial
import time

import threading
import numpy as np
import face_recognition
import os
from PIL import Image, ImageDraw, ImageFont
import sounddevice as sd
import wavio
import requests

__author__ = "Mariana Dinis, Sofia Vidal, Carolina Pires"

class Arduino(threading.Thread):
    """Classe para comunicação com o Arduino e execução de tarefas relacionadas."""
    def __init__(self, email,mensagem):
        """
        Inicializa uma nova instância da classe Arduino.

        Parâmetros:
            email (str): O endereço de e-mail do destinatário das notificações.
            mensagem (str): A mensagem personalizada do dono do sistema.

        """
        # Chama o construtor da classe pai
        super().__init__()
        
        # Inicializa a porta serial com o dispositivo Arduino
        nome_porta = '' # inicializa uma variável para armazenar o nome da porta
        for porta in ['/dev/ttyACM0', '/dev/ttyACM1', '/dev/ttyACM2']:
            if os.path.exists(porta): # verifica se a porta existe no sistema operacional
                nome_porta = porta # armazena o nome da porta serial encontrada
                break # interrompe o loop assim que uma porta válida é encontrada

        if not nome_porta: # verifica se nenhuma porta válida foi encontrada
            print("Erro. Arduino não conectado!") # mensagem de erro que indica que o Arduino não está conectado
            sys.exit(1) # encerra o programa com código de erro 1
            
        self.serial = serial.Serial(nome_porta, 9600) # inicializa a comunicação serial com o Arduino
        
        # Define o link para captura de imagem da câmera
        self.link = "http://192.168.126.112/cam-hi.jpg"
        
        # Define a thread como daemon para que ela termine quando o programa principal terminar
        self.daemon = True
        
        # Armazena o endereço de e-mail
        self.email = email

        # Armazena a mensagem do dono
        self.mensagem_dono = mensagem


    def run(self):
        """Método executado quando a thread é iniciada."""
        # Método chamado quando a thread é iniciada
        self.DoArduino()


    def stop(self):
        """Encerra a thread."""
        # Método para encerrar a thread
        self.serial.close()  # Fecha a porta serial


    def EnviaNotif(self, corpo="Olá, isto é um teste", caminho=os.path.join(os.path.dirname(__file__), "NovasCaras", "captura1.jpg")):
        """
        Envia uma notificação por e-mail com um corpo de mensagem e um arquivo anexado.

        Parâmetros:
            corpo (str): O corpo da mensagem a ser enviado no e-mail.
            caminho (str): O caminho para o arquivo a ser anexado ao e-mail.

        """
        # Configurações de email
        email_admin = "campainha.inteligente.iad@gmail.com" # email do remetente
        password = "errn xfzo dijr lorc " # password do email do remetente para iniciar sessão
        
        # Email do destinatário
        email_utilizador = self.email  
        
        # Caminho para o arquivo a ser anexado
        ficheiro = caminho
        
        # Criação do objeto de mensagem
        msg = MIMEMultipart()
        msg['From'] = email_admin #define o email do remetente
        msg['To'] = email_utilizador #define o email do destinatário
        msg['Subject'] = "Notificação" #define o assunto do email

        # Adiciona o corpo da mensagem
        msg.attach(MIMEText(str(corpo), 'plain'))

        # Adiciona o arquivo como anexo
        part = MIMEBase('application', "octet-stream")  # Cria um objeto MIMEBase para o tipo de conteúdo "octet-stream"
        part.set_payload(open(ficheiro, "rb").read())  # Define o conteúdo do anexo como o conteúdo do arquivo binário especificado
        encoders.encode_base64(part)  # Codifica o conteúdo do anexo em base64 para garantir que possa ser enviado por email
        part.add_header('Content-Disposition', f'attachment; filename="{ficheiro}"')  # Adiciona o cabeçalho Content-Disposition ao anexo
        msg.attach(part)  # Anexa o objeto MIMEBase à mensagem de email


        # Converte a mensagem para string
        email_msg = msg.as_string()

        # Conexão com o servidor SMTP e envio do email
        session = smtplib.SMTP_SSL('smtp.gmail.com', 465) # Inicia uma sessão SMTP_SSL com o servidor do Gmail
        session.login(email_admin, password) # Faz login na conta do Gmail
        session.sendmail(email_admin, email_utilizador, email_msg) # Envia o email
        session.quit() # Fecha a conexão com o servidor SMTP


    def CamaraFrame(self, nome_ficheiro="captura1.jpg", nome_diretorio="NovasCaras"):
        """
        Captura uma imagem da câmera e realiza reconhecimento facial.

        Parâmetros:
            nome_ficheiro (str): O nome do arquivo de imagem a ser salvo.
            nome_diretorio (str): O nome do diretório onde o arquivo será salvo.

        """
        # Obtém o caminho do diretório do script atual
        script_dir = os.path.dirname(os.path.abspath(__file__))

        # Constrói o caminho completo para o diretório
        caminho_diretorio = os.path.join(script_dir, nome_diretorio)

        # Certifica-se de que o diretório existe
        if not os.path.exists(caminho_diretorio):
            os.makedirs(caminho_diretorio) # Se não existir o diretório, este é criado

        # Constrói o caminho completo para o arquivo
        caminho_ficheiro = os.path.join(caminho_diretorio, nome_ficheiro)

        # Faz download da imagem do URL
        resposta = requests.get(self.link)
        if resposta.status_code == 200:  # Verifica se o download foi bem-sucedido
            # Guarda a imagem no arquivo especificado
            with open(caminho_ficheiro, "wb") as fp:
                fp.write(resposta.content)
            print("Download da imagem feito com sucesso.") # Exibe uma mensagem se o download foi executado com sucesso
            self.ReconhecimentoFacial()  # Chama a função de reconhecimento facial
        else:
            # Se o download falhar, exibe uma mensagem de erro com o código de status HTTP
            print(f"Falha ao fazer o download da imagem. Estado: {resposta.status_code}")


    def ReconhecimentoFacial(self, img1= os.path.join(os.path.dirname(__file__), "Caras/dono.png"), img2=os.path.join(os.path.dirname(__file__), "NovasCaras/captura1.jpg")):
        """
        Realiza o reconhecimento facial comparando duas imagens.

        Parâmetros:
            img1 (str): O caminho da imagem de referência.
            img2 (str): O caminho da imagem de teste.

        """   
        # Carregar e codificar a imagem de referência (img1)
        imgDono = face_recognition.load_image_file(img1)
        encodeDono = face_recognition.face_encodings(imgDono)[0]

        # Carregar e codificar a imagem de teste (img2)
        imgTeste = face_recognition.load_image_file(img2)
        localizacao_cara = face_recognition.face_locations(imgTeste)

        # Verificar se foram detectadas faces na imagem de teste
        if len(localizacao_cara) != 0:
            # Obter as codificações das faces detectadas na imagem de teste
            visitante_encodings = face_recognition.face_encodings(imgTeste, localizacao_cara)

            # Definir as codificações e os nomes das faces conhecidas
            encodings_cara_conhecida = [encodeDono]
            nome_cara_conhecida = ["Dono"]

            # Criar uma imagem Pillow a partir da matriz da imagem de teste
            imgTeste = Image.fromarray(imgTeste)
            desenho = ImageDraw.Draw(imgTeste) 
            fontsize = 11 # Define o tamanho da letra
            fonte = ImageFont.load_default()

            # Iterar sobre as localizações das caras detectadas e as codificações correspondentes
            for (top, right, bottom, left), face_encoding in zip(localizacao_cara, visitante_encodings):
                # Comparar as codificações da cara detectada com as faces conhecidas
                corresp = face_recognition.compare_faces(encodings_cara_conhecida, face_encoding)

                # Definir o nome da cara como "Desconhecido" por padrão
                nome = "Desconhecido"

                # Se uma correspondência for encontrada, atribuir o nome correspondente
                if True in corresp:
                    corresp_index = corresp.index(True)
                    nome = nome_cara_conhecida[corresp_index] # atribuição do nome do dono à cara

                # Desenhar um retângulo em torno da face
                desenho.rectangle(((left, top), (right, bottom)), outline=(48, 63, 159), width=1)

                # Desenhar um retângulo de fundo para o texto do nome
                largura_texto, altura_texto = 40, 10 # Define os tamanhos do texto
                desenho.rectangle(((left, bottom - altura_texto - 10), (right, bottom)), fill=(48, 63, 159), outline=(48, 63, 159))
                # Desenhar o texto do nome
                desenho.text((left + 6, bottom - altura_texto - 5), nome, fill=(255, 255, 255, 0), font=fonte)

            # Guardar a imagem modificada
            caminho_img = os.path.join(os.path.dirname(__file__), "visitante.jpg")
            imgTeste.save(caminho_img)

            print("Imagem guardada:", caminho_img) # Exibe uma mensagem a informar que a imagem foi guardada e onde

        else:
            # Se nenhuma cara for detectada, guardar a imagem original
            print("Nenhuma cara detectada") # Exibe uma mensagem a informar que nenhuma cara foi detetada
            caminho_img = os.path.join(os.path.dirname(__file__), "visitante.jpg") # Define o caminho para guardar a imagem
            imgTeste = Image.open(img2) # Define a imagem a guardar
            imgTeste.save(caminho_img) # Guarda a imagem


    def DoArduino(self):
        """Executa operações do Arduino de acordo com mensagens recebidas."""
        while True:  # Loop infinito para verificar continuamente os dados disponíveis
            if self.serial.in_waiting > 0:  # Verifica se há dados disponíveis para leitura
                mensagem = self.serial.readline().decode().strip()  # Lê a mensagem do Arduino e a decodifica
                ficheiro1 = os.path.join(os.path.dirname(__file__), "visitante.jpg") # Define o caminho da imagem do visitante
                ficheiro2 = os.path.join(os.path.dirname(__file__), "recorded_audio.wav") # Define o caminho do segundo ficheiro audio

                if mensagem == "1":  
                    self.CamaraFrame()  # Captura uma imagem e faz reconhecimento facial
                    mensagem1 = "A sua campainha tocou 1 vez. Veja quem está à porta"  # Mensagem para notificação
                    self.EnviaNotif(mensagem1, ficheiro1)  # Envia a notificação com a imagem capturada
                    time.sleep(5)  # Aguarda 5 segundos

                elif mensagem == "3":  
                    mensagem3 = "A sua campainha tocou 3 vezes. Ouça aqui a mensagem de voz que o visitante lhe deixou"  # Mensagem para notificação
                    texto = "Grave uma nota de voz"  # Texto a ser enviado para o Arduino
                    self.serial.write(texto.encode())  # Envia o texto para o Arduino
                    time.sleep(10)  # Aguarda 10 segungos

                    try:
                        ser = serial.Serial("/dev/tty1", 9600)  # Abre a porta serial para comunicação com o microfone
                        if ser.isOpen():  # Verifica se a porta está aberta
                            print(f"A porta está aberta.")

                        duracao = 5  # Duração da gravação em segundos
                        taxa_amostras = 44100  # Taxa de amostragem
                        canais = 1  # Número de canais de áudio (mono)

                        texto2 = "Gravando..."  # Texto para indicar a gravação
                        self.serial.write(texto2.encode())  # Envia o texto para o Arduino
                        time.sleep(8)  # Aguarda 8 segundos

                        audio_dados = sd.rec(int(duracao * taxa_amostras), samplerate=taxa_amostras, channels=canais, dtype='int16')  # Grava áudio
                        sd.wait()  # Aguarda a conclusão da gravação
                        time.sleep(10)  # Aguarda 10 segundos

                        diretorio = os.path.join(os.path.dirname(__file__))  # Diretório de destino do arquivo de áudio
                        nome_ficheiro = os.path.join(diretorio, "recorded_audio.wav")  # Define o nome do arquivo de áudio
                        wavio.write(nome_ficheiro, audio_dados, taxa_amostras, sampwidth=2)  # Guarda o arquivo de áudio

                        time.sleep(3)  # Aguarda 3 segundos
                        texto3 = "Enviado"  # Texto para indicar que o arquivo foi enviado
                        self.serial.write(texto3.encode())  # Envia o texto para o Arduino
                        self.EnviaNotif(mensagem3, ficheiro2)  # Envia a notificação com o arquivo de áudio
                        ser.close()  # Fecha a porta serial
                        print(f"A porta está fechada.")
                        self.serial.reset_input_buffer() # Apaga os dados enviados pelo serial até então
                        texto4=self.mensagem_dono # Definição da mensagem a mostrar no LCD
                        self.serial.write(texto4.encode()) # Envia a mensagem do dono inicial pelo serial
                        
                    except serial.SerialException as e:
                        print(f"Erro ao abrir a porta: {e}")  # Trata exceções de abertura de porta serial

                elif eval(mensagem) >= 5:  # Se a mensagem for maior ou igual a 5
                    mensagem5 = "A sua campainha tocou 5 ou mais vezes. SPAM detetado"  # Mensagem para notificação
                    self.EnviaNotif(mensagem5, ficheiro1)  # Envia a notificação com a imagem capturada

                else:  # Se nenhuma das condições acima for atendida
                    print("fim")  # Exibe "fim"

