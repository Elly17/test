### Настройка безопасного подключения

Добавляем нового пользователя
```bash
useradd -G sudo -m vpnuser -s /bin/bash 
```
Ставим пасс
```bash
passwd vpnuser
```
Переключаемся на пользователя 
```bash
su vpnuser
```

Создаем ssh ключ на клиенте с ос windows & linux команды одни
Ключи храняться в /home/user/.ssh 
Обязательно ставим пароль при генерации ключа
```bash
ssh-keygen
```

Используем ssh-copy-id для передачи публичного ключа на наш сервер
Если нужно загружать конкретный ключ используем -i key_file vpnuser@server_ip
На windows публичный ключ копируем вручную сюда echo *Text* >> ~/.ssh/authorized_keys
```bash
ssh-copy-id vpnuser@server_ip 
```

Отключаем вход по логину и паролю и меняем порт на ssh
```bash
nano /etc/ssh/sshd_config
```

PermitRootLogin no
PasswordAuthentication no
port 22 //заменяем
обратить внимание на подарочки от хостера в  /etc/ssh/sshd_config.d/*.conf

перезапускаем службу
```bash
systemcte restart sshd
```
