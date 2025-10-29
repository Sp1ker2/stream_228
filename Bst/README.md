# 📹 Screen Monitor - Система мониторинга экранов

Система для мониторинга экранов множества машин с централизованным сервером.

## 🏗️ Архитектура

```
50+ Windows/Mac/Linux машин → Сервер (195.133.17.131:6789)
                                ↓
                          temp_recordings/
                          ├── Машина1/
                          ├── Машина2/
                          └── ...
```

## 🚀 Быстрый старт

### На сервере:

```bash
# Развертывание на удаленном сервере
export REMOTE_PASS='ваш_пароль'
./deploy_server.sh
```

### На клиенте (Mac/Linux):

```bash
export MACHINE_ID="Моя_Машина"
export SERVER_HOST="195.133.17.131"
export SERVER_PORT="6789"
source venv/bin/activate
python3 client_live.py
```

### На клиенте (Windows):

1. Установить Python 3.11+
2. Запустить `install_windows.bat`
3. Настроить `config.txt` с уникальным `MACHINE_ID`
4. Запустить `start_client.bat`

## 📁 Структура проекта

### Основные файлы:

**Сервер:**
- `server_simple.py` - основной сервер (веб-интерфейс, live стримы, хранение видео)
- `requirements.txt` - зависимости для сервера

**Клиент Mac/Linux:**
- `client_live.py` - клиент с live стримом

**Клиент Windows:**
- `client_live_windows.py` - клиент для Windows (использует mss)
- `requirements_windows.txt` - зависимости для Windows
- `install_windows.bat` - установка зависимостей
- `start_client.bat` - запуск клиента
- `config.example.txt` - шаблон конфигурации

**Docker (для тестирования):**
- `Dockerfile.client` - образ клиента
- `docker-compose.yml` - запуск нескольких клиентов

**Развертывание:**
- `deploy_server.sh` - развертывание на удаленный сервер
- `OPEN_PORT.sh` - открытие порта на сервере
- `start_all.sh` / `stop_all.sh` - управление всей системой
- `START_MY_MACHINE.sh` - запуск локальной машины

**Документация:**
- `README_WINDOWS.md` - подробная инструкция для Windows
- `АРХИТЕКТУРА_50_МАШИН_WINDOWS.txt` - архитектура системы
- `START_AND_FINISH.txt` - инструкции по запуску/остановке

**Конфигурация:**
- `config.example.sh` - пример конфига для сервера
- `SERVER_CONFIG.txt` - информация о сервере

## 🌐 Веб-интерфейс

Откройте в браузере:
```
http://195.133.17.131:6789
```

Показывает:
- Список всех машин
- Live стрим каждой машины (`/live/{MACHINE_ID}`)
- Записи видео (`/list/{MACHINE_ID}`)

## 📦 Установка зависимостей

### Сервер:

```bash
pip install -r requirements.txt
```

### Windows клиент:

```bash
pip install -r requirements_windows.txt
```

### Mac/Linux клиент:

```bash
pip install -r requirements.txt
```

## ⚙️ Конфигурация

### Windows:

Создайте `config.txt`:
```txt
MACHINE_ID=Иван_Desktop
SERVER_HOST=195.133.17.131
SERVER_PORT=6789
SIMULATE_SCREEN=false
```

### Mac/Linux:

```bash
export MACHINE_ID="Иван_Desktop"
export SERVER_HOST="195.133.17.131"
export SERVER_PORT="6789"
```

## 🔧 Управление

```bash
# Запустить все (сервер + локальная машина)
./start_all.sh

# Остановить все
./stop_all.sh

# Только локальная машина
./START_MY_MACHINE.sh
```

## 📝 Важно

1. Каждая машина должна иметь **уникальный** `MACHINE_ID`
2. Все машины должны иметь доступ к серверу
3. Порт 6789 должен быть открыт на сервере
4. Видео сохраняются локально на каждой машине (не загружаются на сервер)

## 📞 Поддержка

См. подробные инструкции:
- Windows: `README_WINDOWS.md`
- Архитектура: `АРХИТЕКТУРА_50_МАШИН_WINDOWS.txt`
- Запуск/остановка: `START_AND_FINISH.txt`
