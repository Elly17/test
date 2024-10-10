[Источник](https://habr.com/ru/articles/758570/)  

Настройка сервера Cloak
Настройка сервера будет производится на примере Debian 11 (amd64)

Для начала нам нужно скачать исполняемый файл с сайта проекта на [Github](https://github.com/cbeuw/Cloak/releases)
```bash
wget https://github.com/cbeuw/Cloak/releases/download/v2.7.0/ck-server-linux-amd64-v2.7.0 -O ck-server
```
Делаем файл исполняемым:

```bash
chmod +x ck-server
```

Переносим файл в /usr/bin (требует прав root)

```bash
sudo mv ck-server /usr/bin/ck-server
```
Далее нам необходимо сгенерировать публичный и приватный ключи доступа Cloak

```bash
/usr/bin/ck-server -key
```
Получаем

```bash
Your PUBLIC key is:                      dnc7/Tbif51pXZ6EcWwc2367rHAbzVOzlzJ4qyS1uC4=
Your PRIVATE key is (keep it secret):    ULn0VAREq6zgk3kVOUYTbauwhKOGK48nRDibL5wLans=
```

Сохраняем эти данные, они понадобятся чуть позже.

Далее нам необходимо сгенерировать UID Пользователя и Администратора

```bash
/usr/bin/ck-server -uid
/usr/bin/ck-server -uid
```
На выходе получаем два UID: Пользователя и Администратора

```bash
Your UID is: w2S8IMf/T4/TAC7MJZQlWw== #Пользователь USER_UID1
Your UID is: 9bNJTRNEaN3iwljIAT2U+Q== #Администратор ADMIN_UID
```
Сохраняем эти данные.

UID для следующих пользователей генерируются тем же образом, путём запуска команды.

Так же необходимо уточнить параметры вашего сервера OpenVPN, например, так

```bash
sudo cat /etc/openvpn/server.conf
```
в примере это OpenVPN UDP и порт 51000.

Далее подготавливаем конфигурацию сервера /etc/cloak/ckserver.json

Создадим папку и файл следующего содержания

```bash
sudo mkdir /etc/cloak
sudo nano /etc/cloak/ckserver.json
```
/etc/cloak/ckserver.json:

```bash
{
  "ProxyBook": {
    "openvpn": [
      "udp",
      "127.0.0.1:51000"
    ]
  },
  "BindAddr": [
    ":443",
    ":80"
  ],
  "BypassUID": [
    "w2S8IMf/T4/TAC7MJZQlWw=="
  ],
  "RedirAddr": "dzen.ru",
  "PrivateKey": "ULn0VAREq6zgk3kVOUYTbauwhKOGK48nRDibL5wLans=",
  "AdminUID": "9bNJTRNEaN3iwljIAT2U+Q==",
  "DatabasePath": "userinfo.db"
}
```
Сюда вводим ваши полученные ранее значения.

В примере это:

"ProxyBook": "openvpn" - вводим "udp" и порт 51000

В "PrivateKey" ULn0VAREq6zgk3kVOUYTbauwhKOGK48nRDibL5wLans=

В "AdminUID" 9bNJTRNEaN3iwljIAT2U+Q==

В "BypassUID" w2S8IMf/T4/TAC7MJZQlWw== (при наличии нескольких пользователей каждый UID вводится в кавычках на отдельной строке, через запятую как в [примере](https://github.com/cbeuw/Cloak/blob/master/example_config/ckserver.json))

Сохраняем изменения.

Далее создаём службу systemd для автозапуска:

```bash
sudo nano /etc/systemd/system/cloak-server.service
```
/etc/systemd/system/cloak-server.service:

```bash
[Unit]
Description=cloak-server
After=network.target
StartLimitIntervalSec=0
[Service]
Type=simple
#Service variables
Environment=CONFIG="/etc/cloak/ckserver.json"
ExecStart=/usr/bin/ck-server -c "$CONFIG"
Restart=always
[Install]
WantedBy=multi-user.target
```
Сохраняем изменения.

Перезагружаем список служб, активируем автозапуск и запускаем службу:

```bash
sudo systemctl daemon-reload
sudo systemctl enable cloak-server.service
sudo systemctl start cloak-server.service
```
Так же необходимо будет убедится что у вас открыты порты 80 и 443, в настройках UFW или вашего внешнего файрволла.

Так же необходимо внести изменения в конфигурацию вашего сервера OpenVPN

Убедитесь что в конфигурации /etc/openvpn/server.conf присутствуют следующие строки:

```bash
# So that OpenVPN is listening to ck-server
local 127.0.0.1
# UDP support is experimental at the moment. Change the line below to proto tcp if it's not working well
proto udp
dev tun

```
local 127.0.0.1 означает что OpenVPN сервер теперь будет слушать только на локальном интерфейсе и все клиенты должны будут подключаться через Cloak.

Затем добавьте строку, чтобы базовые соединения между ck-client и ck-server отправлялись через физический интерфейс, а не возвращались обратно через OpenVPN

```bash
route <ip удаленного vpn сервера> 255.255.255.255 ip шлюза
```
Переходим к настройке клиента.
Определяем архитектуру:
```bash
cat /sys/devices/system/cpu/modalias | grep -r -E -o ".{0,4}type.{0,6}"
```
Скачиваем по ссылке на роутер при помощи wget:

```bash
wget https://github.com/cbeuw/Cloak/releases/download/v2.7.0/ck-client-linux-mipsle_softfloat-v2.7.0 -O ck-client
```
Разрешаем запуск исполняемого файла:

```bash
chmod +x /tmp/ck-client
```
Проверяем работу программы:

```bash
./ck-client --help
```
Далее перенесём файл ck-client в /usr/bin (ПЗУ) (Файл займет около 9Мб)

```bash
mv /tmp/ck-client /usr/bin/ck-client
```

Далее подготавливаем конфигурацию клиента.

Создадим папку конфигурации

```bash
mkdir /etc/config/cloak
```

И сам файл

/etc/config/cloak/ckclient.json:

```bash
{
"Transport": "direct",
"ProxyMethod": "openvpn",
"EncryptionMethod": "aes-gcm",
"UID": "w2S8IMf/T4/TAC7MJZQlWw==",
"PublicKey": "dnc7/Tbif51pXZ6EcWwc2367rHAbzVOzlzJ4qyS1uC4=",
"ServerName": "dl.google.com",
"NumConn": 4,
"BrowserSig": "chrome",
"StreamTimeout": 300
}
```

