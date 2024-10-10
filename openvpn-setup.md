## Создаем собственный VPN-сервер
[Источник](https://www.reg.ru/blog/sozdayem-sobstvennyy-vpn-server/)

## 
### Установка пакетов

Обновляем пакеты
```bash
sudo apt update
```
Устанавливаем пакеты
```bash
sudo apt install openvpn easy-rsa net-tools
```

### Настройка удостоверяющего центра

Разворачиваем на сервере центр сертификаций и генерируем корневой сертификат.<br>
Для этого:

1. Копируем файлы в папку `/etc/openvpn/` и переходим в нее
```bash
sudo cp -R /usr/share/easy-rsa /etc/openvpn/
cd /etc/openvpn/easy-rsa
```
2. Создаем удостоверяющий центр и корневой сертификат
```bash
export EASYRSA=$(pwd)  
sudo ./easyrsa init-pki  
sudo ./easyrsa build-ca
```
После ввода последней команды будет предложено ввести кодовую фразу.
Указанный пароль в дальнейшем будет использоваться для подписи сертификатов и ключей.<br>
Должно появиться два файла:
* `/etc/openvpn/easy-rsa/pki/ca.crt` — сертификат CA
* `/etc/openvpn/easy-rsa/pki/private/ca.key` — приватный ключ CA.

1. Создаем директорию, в которой будут храниться ключи и сертификаты:
```bash
mkdir /etc/openvpn/certs/
```
2. Перемещаем в созданную папку сертификат CA:
```bash
cp /etc/openvpn/easy-rsa/pki/ca.crt /etc/openvpn/certs/ca.crt
```

### Создание запроса сертификата и закрытого ключа сервера

1. Создаем закрытый ключ для сервера и файл запроса сертификата:
```bash
./easyrsa gen-req server nopass
```
2. Подписываем созданный сертификат ключом сертификационного центра:
```bash
./easyrsa sign-req server server
```
Вводим "yes" и нажимаем Enter. После вводим кодовую фразу, которую задали при
настройке удостоверяющего центра.

3. Копируем сгенерированный сертификат и ключ в директорию `/etc/openvpn/certs/`:
```bash
cp /etc/openvpn/easy-rsa/pki/issued/server.crt /etc/openvpn/certs/
cp /etc/openvpn/easy-rsa/pki/private/server.key /etc/openvpn/certs/
```
4. Сгенерируем файл параметров Diffie–Hellman:
```bash
openssl dhparam -out /etc/openvpn/certs/dh2048.pem 2048
```
5. Создаем ключ HMAC c помощью команды:
```bash
openvpn --genkey --secret /etc/openvpn/certs/ta.key
```
Теперь в директорий `/etc/openvpn/certs/` должно быть 5 файлов. Проверить это можно с помощью `ls`:
```bash
ls -l /etc/openvpn/certs/
```
Ожидаемый вывод
```bash
--rw------- 1 root root 1204 Aug 28 22:03 ca.crt
--rw-r--r-- 1 root root  423 Aug 28 22:03 dh2048.pem
--rw------- 1 root root 4608 Aug 28 22:03 server.crt
--rw------- 1 root root 1704 Aug 28 22:03 server.key
--rw------- 1 root root  636 Aug 28 22:03 ta.key
```

### Создание ключей клиентов OpenVPN

1. Генерируем закрытый ключ и запрос сертификата клиента
```bash
./easyrsa gen-req client1 nopass
```
2. Подписываем запрос
```bash
./easyrsa sign-req client client1
```
Вводим "yes" и нажимаем Enter. Затем вводим кодовую фразу, которую задали при настройке удостоверяющего центра.

## Запуск сервера OpenVPN

1. Вводим команду:
```bash
nano /etc/openvpn/server.conf
```
2. Копируем содержимое
```
# Порт для OpenVPN
port 1194
 
# Протокол, который использует OpenVPN
;proto tcp
proto udp
 
# Интерфейс
;dev tap
dev tun
 
# Ключи
 
# Сертификат CA
ca /etc/openvpn/certs/ca.crt
# Сертификат сервера
cert /etc/openvpn/certs/server.crt
# Приватный ключ сервера
key /etc/openvpn/certs/server.key #не распространяется и хранится в секрете
 
# параметры Diffie Hellman
dh /etc/openvpn/certs/dh2048.pem
 
# Создание виртуальной сети и ее параметры
# Network topology
topology subnet

# IP и маска подсети
server 10.8.0.0 255.255.255.0
 
# После перезапуска сервера клиенту будет выдан прежний IP
ifconfig-pool-persist /etc/openvpn/ipp.txt
 
# Установка шлюза по умолчанию
push "redirect–gateway def1 bypass–dhcp"
 
# Разрешить использовать нескольким клиентами одну и ту же пару ключей
# не рекомендуется использовать, закомментирована
;duplicate–cn
 
# Пинговать удаленный узел с интервалом в 10 секунд
# Если узел не отвечает в течение 120 секунд, то будет выполнена попытка повторного подключения к клиенту
keepalive 10 120
 
# Защита от DoS–атак портов UDP с помощью HMAC 
remote-cert-tls client
tls-auth /etc/openvpn/certs/ta.key 0 # файл хранится в секрете
 
# Криптографические шифры
cipher CHACHA20-POLY1305 #для клиентов нужно указывать такой же, AES-256-GCM, AES-128-GCM, and CHACHA20-POLY1305
 
# Сжатие и отправка настроек клиенту
;compress lz4–v2
;push "compress lz4–v2"
 
# Максимальное число одновременных подключений
;max–clients 100
 
# Понижение привилегий демона OpenVPN
# после запуска
# Не использовать для Windows
;user nobody
;group nobody
 
# При падении туннеля не выключать интерфейсы, не перечитывать ключи
persist-key
persist-tun
 
# Лог текущих соединений
# Каждую минуту обрезается и перезаписываться
status openvpn–status.log
 
# Логи syslog
# Используется только один. Раскомментировать необходимый
 
# перезаписывать файл журнала при каждом запуске OpenVPN
;log openvpn.log
 
# дополнять журнал
;log–append openvpn.log
 
# Уровень вербальности
#
# 0 тихий, кроме фатальных ошибок
# 4 подходит для обычного использования
# 5 и 6 помогают в отладке при решении проблем с подключением
# 9 крайне вербальный
verb 4
 
# Предупреждение клиента о перезапуске сервера
explicit-exit-notify 1
```
<span style="color:red">
Обратите внимание! Если подсеть 10.8.0.0/24 уже занята, то в параметре server нужно указать другой IP-адрес, например, 10.10.0.0.
</span><br>
Сохраняем изменения.

### Проверка работы сервера OpenVpn

1. Проверить работу сервера можно с помощью команды:
```bash
openvpn /etc/openvpn/server.conf
```
Если все работает, то должно быть сообщение "Initialization Sequence Completed":
```bash
Wed Aug 31 22:22:50 2024 us=720160 Initialization Sequence Completed
```
2. Если ошибок нет, запускаем службу OpenVPN и добавляем ее в автозагрузку
```bash
systemctl start openvpn@server.service
systemctl enable openvpn@server.service
```
3. Проверяем, работает ли служба, с помощью команды
```bash
systemctl status openvpn@server.service
```
Должен быть вывод: Active: active(running)

### Включение маршрутизаций трафика на OpenVPN-сервере

Необходимо настроить маршрутизацию трафика для доступа к глобальной сети. Для этого:
1. Создайте директорию `/root/bin`:
```bash
mkdir /root/bin
```
2. Вводим команду:
```bash
nano /root/bin/vpn_route.sh
```
3. добавляем в файл конфигурацию
```bash
#!/bin/sh
 
# Сетевой интерфейс для выхода в интернет
DEV='eth0'
 
# Значение подсети
PRIVATE=10.8.0.0/24
 
if [ -z "$DEV" ]; then
DEV="$(ip route | grep default | head -n 1 | awk '{print $5}')"
fi
# Маршрутизация транзитных IP-пакетов
sysctl net.ipv4.ip_forward=1
# Проверка блокировки перенаправленного трафика iptables 
iptables -I FORWARD -j ACCEPT
 
# Преобразование адресов (NAT) 
 
iptables -t nat -I POSTROUTING -s $PRIVATE -o $DEV -j MASQUERADE
```
Если при создании конфигурационного файла OpenVPN задавалась подсеть, отличная от 10.8.0.0/24,
то необходимо указать свое значение подсети в параметре PRIVATE.

В параметре DEV нужно указать сетевой интерфейс, который используется для выхода в интернет.
Узнать его можно с помощью команды:
```bash
route | grep '^default' | grep -o '[^ ]*$'
```
4. Задаем права для файла:
```bash
chmod 755 /root/bin/vpn_route.sh
```
5. Выполняем тестовый запуск скрипта:
```bash
bash /root/bin/vpn_route.sh
```
6. Если ошибок нет, добавляем скрипт в автозагрузку. Для этого создаем файл:
```bash
nano /etc/systemd/system/openvpn-server-routing.service
```
7. Добавляем в него:
```
[Unit]
Description=Включение маршрутизации OpenVPN трафика.
[Service]
ExecStart=/root/bin/vpn_route.sh
[Install]
WantedBy=multi-user.target
```
8. Добавляем созданную службу в автозагрузку
```bash
systemctl enable openvpn-server-routing
```

### Настройка клиента OpenVPN

Теперь необходимо создать файл конфигураций .ovpn для подключения клиента к VPN.
Для этого открываем текстовый редактор и добавляем в файл конфигурацию:

```
# Роль 
client
 
# IP сервера OpenVPN 
remote 123.123.123.123
 
# Порт сервера OpenVPN, как в конфигурации сервера
port 1194 
 
# Интерфейс
dev tun


# Протокол OpenVPN, как на сервере
;proto tcp
proto udp
 
# Имя хоста, IP и порт сервера 
 
;remote my–server–1 1194
;remote my–server–2 1194
 
# Случайный выбор хостов. Если не указано, берется по порядку
;remote–random
 
# Преобразование имени хоста 
# (в случае непостоянного подключения к интернету)
resolv-retry infinite
 
# Привязка к локальному порту
nobind
 
# Шлюз по умолчанию 
redirect-gateway def1 bypass-dhcp
 
# При падении туннеля не выключать интерфейсы, не перечитывать ключи
persist-key
persist-tun
 
# Настройка HTTP прокси при подключении OpenVPN серверу
;http–proxy–retry # retry on connection failures
;http–proxy [proxy server] [proxy port #]
 
# Отключение предупреждений о дублировании пакетов
;mute–replay–warnings
 
# Дополнительная защита
remote-cert-tls server 
 
# Ключ HMAC
key-direction 1
 
# Шифрование
cipher CHACHA20-POLY1305 #для клиентов нужно указывать такой же, AES-256-GCM, AES-128-GCM, and CHACHA20-POLY1305
 
# Сжатие. Если на сервере отключено, не включается
#comp–lzo
 
# Вербальность журнала
verb 3
 
# Сертификаты
 
<ca>
*Вставьте содержимое файла /etc/openvpn/certs/ca.crt*
</ca>
<cert>
*Вставьте содержимое файла /etc/openvpn/easy-rsa/pki/issued/client1.crt*
</cert>
<key>
*Вставьте содержимое файла /etc/openvpn/easy-rsa/pki/private/client1.key*
</key>
<tls-auth>
*Вставьте содержимое файла /etc/openvpn/certs/ta.key*
</tls-auth>
```

В параметре remote вместо 123.123.123.123 указываем IP адрес сервера. В тегах вставляем содержимое сгенерированных ранее файлов

* &lt;ca>&lt;/ca&gt; — вставьте данные из файла `/etc/openvpn/certs/ca.crt`
* &lt;cert>&lt;/cert&gt; — вставьте данные из файла `/etc/openvpn/easy-rsa/pki/issued/client1.crt`
* &lt;key>&lt;/key&gt; — вставьте данные из файла `/etc/openvpn/easy-rsa/pki/private/client1.key`
* &lt;tls-auth>&lt;/tls-auth&gt; — вставьте данные из файла `/etc/openvpn/certs/ta.key`

После внесения всех изменений сохраняем файл с расширением .ovpn.<br>
Чтобы подключится к VPN, необходимо скачать клиент OpenVPN и импортировать в него конфигурационный файл .ovpn.
