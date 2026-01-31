// integratedBleLib.js - 통합된 BLE 연결 라이브러리 (합성 방식)

'use strict';

// -----------------------------------------
// Logging (none / info / debug)
// - none : 로그 없음
// - info : 사용자에게 유의미한 요약 로그
// - debug: 고빈도/정밀 로그(성능 저하 가능)
//
// 사용 예:
//   window.EZ_LOG.setLevel('debug');
//   window.EZ_LOG.setLevel('info');
//   window.EZ_LOG.setLevel('none');
// -----------------------------------------
const EZ_LOG = (() => {
    // Capture native console methods first (avoid recursion if we shadow console later)
    const RAW = {
        log: (typeof console !== 'undefined' && console.log) ? console.log.bind(console) : () => {},
        warn: (typeof console !== 'undefined' && console.warn) ? console.warn.bind(console) : () => {},
        error: (typeof console !== 'undefined' && console.error) ? console.error.bind(console) : () => {},
    };

    const LEVELS = { none: 0, info: 1, debug: 2 };
    const normalize = (level) => {
        if (!level) return 'info';
        const v = String(level).toLowerCase();
        return Object.prototype.hasOwnProperty.call(LEVELS, v) ? v : 'info';
    };

    let _level = 'info';
    try {
        if (typeof window !== 'undefined') {
            _level = normalize(window.EZ_LOG_LEVEL);
        }
    } catch (e) { /* ignore */ }

    const enabled = (minLevel) => LEVELS[_level] >= LEVELS[minLevel];

    const api = {
        getLevel() { return _level; },
        setLevel(level) { _level = normalize(level); return _level; },
        isInfo() { return enabled('info'); },
        isDebug() { return enabled('debug'); },
        info(...args) { if (enabled('info')) RAW.log(...args); },
        debug(...args) { if (enabled('debug')) RAW.log(...args); },
        warn(...args) { if (enabled('info')) RAW.warn(...args); },
        error(...args) { if (enabled('info')) RAW.error(...args); },
    };

    try {
        if (typeof window !== 'undefined') {
            window.EZ_LOG = api;
        }
    } catch (e) { /* ignore */ }

    return api;
})();

// Shadow console log/warn/error inside this file to respect EZ_LOG levels.
// - console.log  -> EZ_LOG.debug(...)
// - console.warn -> EZ_LOG.warn(...)
// - console.error-> EZ_LOG.error(...)
// Other console methods are delegated to the native console.
try {
    if (typeof window !== 'undefined' && window.console) {
        const __NATIVE_CONSOLE__ = window.console;
        // eslint-disable-next-line no-unused-vars
        const console = new Proxy(__NATIVE_CONSOLE__, {
            get(target, prop) {
                if (prop === 'log') return (...args) => EZ_LOG.debug(...args);
                if (prop === 'warn') return (...args) => EZ_LOG.warn(...args);
                if (prop === 'error') return (...args) => EZ_LOG.error(...args);
                const v = target[prop];
                return typeof v === 'function' ? v.bind(target) : v;
            }
        });
    }
} catch (e) {
    // ignore
}

// constants.js 내용을 직접 포함
// -----------------------------------------
// IoT 모드 UUID
// -----------------------------------------
// BLE Service UUIDs
const IOT_SERVICE = '11112222-3333-4444-5555-666677778888';
const SENSOR_SERVICE = '11112222-3333-4444-5555-66667777888c';

// 캐릭터리스틱 UUID 상수 - 직접 접근용
const LED_CHARACTERISTIC = '11112222-3333-4444-5555-666677778889';
const CAM_CHARACTERISTIC = '11112222-3333-4444-5555-66667777888a';
const ULTRA_CHARACTERISTIC = '11112222-3333-4444-5555-66667777888b';
const DHT_CHARACTERISTIC = '11112222-3333-4444-5555-66667777888d';
const SERVO_CHARACTERISTIC = '11112222-3333-4444-5555-66667777888e';
const NEOPIXEL_CHARACTERISTIC = '11112222-3333-4444-5555-66667777888f';
const TOUCH_CHARACTERISTIC = '11112222-3333-4444-5555-666677778890';
const LIGHT_CHARACTERISTIC = '11112222-3333-4444-5555-666677778891';
const BUZZER_CHARACTERISTIC = '11112222-3333-4444-5555-666677778892';
const REPL_CHARACTERISTIC = '11112222-3333-4444-5555-666677778893';
const GYRO_CHARACTERISTIC = '11112222-3333-4444-5555-666677778894';
const DUST_CHARACTERISTIC = '11112222-3333-4444-5555-666677778895';
const DCMOTOR_CHARACTERISTIC = '11112222-3333-4444-5555-666677778896';
const HEART_CHARACTERISTIC = '11112222-3333-4444-5555-666677778897';

// EZMaker 전용 레이저/자이로/기압/CO2/DIY-A/DIY-B/HALL/LCD/EZLIGHT/EZVOLT/EZCURR/HUMAN/EZTHERMAL/EZSOUND/EZWEIGHT/EZDUST 모듈 캐릭터리스틱 (별도 UUID 대역)
const EZ_LASER_CHARACTERISTIC    = '22223333-4444-5555-6666-777788889001';
const EZ_GYRO_CHARACTERISTIC     = '22223333-4444-5555-6666-777788889002';
const EZ_PRESS_CHARACTERISTIC    = '22223333-4444-5555-6666-777788889003';
const EZ_CO2_CHARACTERISTIC      = '22223333-4444-5555-6666-777788889004';
const EZ_DIYA_CHARACTERISTIC     = '22223333-4444-5555-6666-777788889005';
const EZ_DIYB_CHARACTERISTIC     = '22223333-4444-5555-6666-777788889006';
const EZ_HALL_CHARACTERISTIC     = '22223333-4444-5555-6666-777788889007';
const EZ_LCD_CHARACTERISTIC      = '22223333-4444-5555-6666-777788889008';
const EZ_LIGHT_CHARACTERISTIC    = '22223333-4444-5555-6666-777788889009';
const EZ_VOLT_CHARACTERISTIC     = '22223333-4444-5555-6666-77778888900a';
const EZ_CURR_CHARACTERISTIC     = '22223333-4444-5555-6666-77778888900b';
const EZ_HUMAN_CHARACTERISTIC    = '22223333-4444-5555-6666-77778888900c';
const EZ_THERMAL_CHARACTERISTIC  = '22223333-4444-5555-6666-77778888900d';
const EZ_SOUND_CHARACTERISTIC    = '22223333-4444-5555-6666-77778888900e';
const EZ_WEIGHT_CHARACTERISTIC   = '22223333-4444-5555-6666-77778888900f';
const EZ_DUST_CHARACTERISTIC     = '22223333-4444-5555-6666-777788889010';

// -----------------------------------------
// REPL 모드 UUID
// -----------------------------------------
const REPL_SERVICE = '6e400001-b5a3-f393-e0a9-e50e24dcca9e';
const REPL_TX_CHARACTERISTIC = '6e400003-b5a3-f393-e0a9-e50e24dcca9e'; // 보드→클라이언트
const REPL_RX_CHARACTERISTIC = '6e400002-b5a3-f393-e0a9-e50e24dcca9e'; // 클라이언트→보드
const REPL_CONTROL_CHARACTERISTIC = '6e400004-b5a3-f393-e0a9-e50e24dcca9e'; // 모드 제어

// -----------------------------------------
// 모드 식별 상수
// -----------------------------------------
const BOARD_MODE = {
    IOT: 'IOT',
    REPL: 'REPL',
    UNKNOWN: 'UNKNOWN'
};

// -----------------------------------------
// 모드 전환 명령
// -----------------------------------------
const MODE_COMMAND = {
    TO_IOT: 'REPL:OFF',
    TO_REPL: 'REPL:ON',
    STATUS: 'REPL:STATUS'
};

// -----------------------------------------
// EZMaker UART 공통 핀 설정
// - UART 기반 센서(EZWEIGHT, EZDUST 등)가 모두 공유하는 두 개의 핀(42, 14)
// - 쉴드 설계 변경 시 이 상수만 수정하면 전체 UART 센서에 반영된다.
// -----------------------------------------
const EZ_UART_TX_PIN = 42; // 공통 UART TX 계열 (예: D11 / GPIO 42)
const EZ_UART_RX_PIN = 14; // 공통 UART RX 계열 (예: D10 / GPIO 14)

// -----------------------------------------
// EZMaker I2C 공통 핀 설정
// - EZMaker 쉴드의 I2C(SDA/SCL) 포트는 고정 배선되어 있으며, I2C 기반 센서는 이 핀을 공통으로 사용한다.
// - 쉴드 설계 변경 시 이 상수만 수정하면 전체 I2C 센서에 반영된다.
// -----------------------------------------
const EZ_I2C_SDA_PIN = 41; // 공통 I2C SDA (예: D6 / GPIO 41)
const EZ_I2C_SCL_PIN = 40; // 공통 I2C SCL (예: D5 / GPIO 40)

// sensorsModule.js에서 사용하는 객체 형태로도 내보내기
const CHARACTERISTIC_UUIDS = {
    // IoT 모드 특성
    led: LED_CHARACTERISTIC,
    camera: CAM_CHARACTERISTIC,
    light: LIGHT_CHARACTERISTIC,
    ultrasonic: ULTRA_CHARACTERISTIC,
    dht: DHT_CHARACTERISTIC,
    touch: TOUCH_CHARACTERISTIC,
    dust: DUST_CHARACTERISTIC,
    gyro: GYRO_CHARACTERISTIC,
    neopixel: NEOPIXEL_CHARACTERISTIC,
    buzzer: BUZZER_CHARACTERISTIC,
    servo: SERVO_CHARACTERISTIC,
    dcmotor: DCMOTOR_CHARACTERISTIC,
    heart:   HEART_CHARACTERISTIC,
    laser:   EZ_LASER_CHARACTERISTIC,
    ezgyro:  EZ_GYRO_CHARACTERISTIC,
    ezpress: EZ_PRESS_CHARACTERISTIC,
    ezco2:   EZ_CO2_CHARACTERISTIC,
    diya:    EZ_DIYA_CHARACTERISTIC,
    diyb:    EZ_DIYB_CHARACTERISTIC,
    hall:    EZ_HALL_CHARACTERISTIC,
    ezlight: EZ_LIGHT_CHARACTERISTIC,
    ezvolt:  EZ_VOLT_CHARACTERISTIC,
    ezcurr:  EZ_CURR_CHARACTERISTIC,
    human:   EZ_HUMAN_CHARACTERISTIC,
    ezthermal: EZ_THERMAL_CHARACTERISTIC,
    ezsound: EZ_SOUND_CHARACTERISTIC,
    ezweight: EZ_WEIGHT_CHARACTERISTIC,
    ezdust: EZ_DUST_CHARACTERISTIC,
    lcd:     EZ_LCD_CHARACTERISTIC,
    // REPL 모드 특성
    repl: REPL_CHARACTERISTIC,
    replTx: REPL_TX_CHARACTERISTIC,
    replRx: REPL_RX_CHARACTERISTIC,
    replControl: REPL_CONTROL_CHARACTERISTIC
};

// 서비스별 포함 특성 매핑
const SERVICE_CHARACTERISTICS = {
    [IOT_SERVICE]: [LED_CHARACTERISTIC, CAM_CHARACTERISTIC, REPL_CHARACTERISTIC],
    [SENSOR_SERVICE]: [ULTRA_CHARACTERISTIC, DHT_CHARACTERISTIC, SERVO_CHARACTERISTIC,
        NEOPIXEL_CHARACTERISTIC, TOUCH_CHARACTERISTIC, LIGHT_CHARACTERISTIC,
        BUZZER_CHARACTERISTIC, GYRO_CHARACTERISTIC, DUST_CHARACTERISTIC,
        DCMOTOR_CHARACTERISTIC, HEART_CHARACTERISTIC,
        EZ_LASER_CHARACTERISTIC,
        EZ_GYRO_CHARACTERISTIC, EZ_PRESS_CHARACTERISTIC, EZ_CO2_CHARACTERISTIC,
        EZ_DIYA_CHARACTERISTIC, EZ_DIYB_CHARACTERISTIC, EZ_HALL_CHARACTERISTIC,
        EZ_LCD_CHARACTERISTIC, EZ_LIGHT_CHARACTERISTIC, EZ_VOLT_CHARACTERISTIC,
        EZ_CURR_CHARACTERISTIC, EZ_HUMAN_CHARACTERISTIC, EZ_THERMAL_CHARACTERISTIC,
        EZ_SOUND_CHARACTERISTIC, EZ_WEIGHT_CHARACTERISTIC, EZ_DUST_CHARACTERISTIC],
    [REPL_SERVICE]: [REPL_TX_CHARACTERISTIC, REPL_RX_CHARACTERISTIC, REPL_CONTROL_CHARACTERISTIC]
};

// 하위 호환성을 위해 전역 변수로도 노출
window.IOT_SERVICE = IOT_SERVICE;
window.SENSOR_SERVICE = SENSOR_SERVICE;
window.LED_CHARACTERISTIC = LED_CHARACTERISTIC;
window.BUZZER_CHARACTERISTIC = BUZZER_CHARACTERISTIC;
window.SERVO_CHARACTERISTIC = SERVO_CHARACTERISTIC;
window.DCMOTOR_CHARACTERISTIC = DCMOTOR_CHARACTERISTIC;
window.NEOPIXEL_CHARACTERISTIC = NEOPIXEL_CHARACTERISTIC;
window.CAM_CHARACTERISTIC = CAM_CHARACTERISTIC;
window.LIGHT_CHARACTERISTIC = LIGHT_CHARACTERISTIC;
window.ULTRA_CHARACTERISTIC = ULTRA_CHARACTERISTIC;
window.DHT_CHARACTERISTIC = DHT_CHARACTERISTIC;
window.TOUCH_CHARACTERISTIC = TOUCH_CHARACTERISTIC;
window.DUST_CHARACTERISTIC = DUST_CHARACTERISTIC;
window.GYRO_CHARACTERISTIC = GYRO_CHARACTERISTIC;
window.HEART_CHARACTERISTIC = HEART_CHARACTERISTIC;
window.EZ_LASER_CHARACTERISTIC = EZ_LASER_CHARACTERISTIC;
window.EZ_GYRO_CHARACTERISTIC = EZ_GYRO_CHARACTERISTIC;
window.EZ_DIYA_CHARACTERISTIC = EZ_DIYA_CHARACTERISTIC;
window.EZ_DIYB_CHARACTERISTIC = EZ_DIYB_CHARACTERISTIC;
window.EZ_HALL_CHARACTERISTIC = EZ_HALL_CHARACTERISTIC;
window.EZ_LCD_CHARACTERISTIC = EZ_LCD_CHARACTERISTIC;
window.EZ_LIGHT_CHARACTERISTIC = EZ_LIGHT_CHARACTERISTIC;
window.EZ_PRESS_CHARACTERISTIC = EZ_PRESS_CHARACTERISTIC;
window.EZ_CO2_CHARACTERISTIC = EZ_CO2_CHARACTERISTIC;
window.EZ_VOLT_CHARACTERISTIC = EZ_VOLT_CHARACTERISTIC;
window.EZ_CURR_CHARACTERISTIC = EZ_CURR_CHARACTERISTIC;
window.EZ_HUMAN_CHARACTERISTIC = EZ_HUMAN_CHARACTERISTIC;
window.EZ_THERMAL_CHARACTERISTIC = EZ_THERMAL_CHARACTERISTIC;
window.EZ_SOUND_CHARACTERISTIC = EZ_SOUND_CHARACTERISTIC;
window.EZ_WEIGHT_CHARACTERISTIC = EZ_WEIGHT_CHARACTERISTIC;
window.EZ_DUST_CHARACTERISTIC = EZ_DUST_CHARACTERISTIC;
window.REPL_SERVICE = REPL_SERVICE;
window.REPL_CHARACTERISTIC = REPL_CHARACTERISTIC;
window.REPL_TX_CHARACTERISTIC = REPL_TX_CHARACTERISTIC;
window.REPL_RX_CHARACTERISTIC = REPL_RX_CHARACTERISTIC;
window.REPL_CONTROL_CHARACTERISTIC = REPL_CONTROL_CHARACTERISTIC;
window.BOARD_MODE = BOARD_MODE;
window.MODE_COMMAND = MODE_COMMAND;
window.CHARACTERISTIC_UUIDS = CHARACTERISTIC_UUIDS;
window.SERVICE_CHARACTERISTICS = SERVICE_CHARACTERISTICS;
window.EZ_UART_TX_PIN = EZ_UART_TX_PIN;
window.EZ_UART_RX_PIN = EZ_UART_RX_PIN;
window.EZ_I2C_SDA_PIN = EZ_I2C_SDA_PIN;
window.EZ_I2C_SCL_PIN = EZ_I2C_SCL_PIN;

/**
 * BLE 명령어 큐 클래스
 * GATT 작업의 동시 실행 방지를 위한 큐 시스템
 */
class BLECommandQueue {
    constructor() {
        this.queue = [];
        this.processing = false;
        this.debug = true; // 디버깅 로그 활성화
    }

    // 명령어를 큐에 추가
    enqueue(command) {
        if (this.debug) console.log(`[BLEQueue] 명령어 큐에 추가: ${command.name || 'unnamed'}`);

        return new Promise((resolve, reject) => {
            this.queue.push({
                command: command,
                resolve: resolve,
                reject: reject,
                name: command.name || 'command-' + this.queue.length
            });

            // 큐가 현재 처리 중이 아니면 처리 시작
            if (!this.processing) {
                this.processQueue();
            } else if (this.debug) {
                console.log(`[BLEQueue] 큐가 처리 중입니다. ${this.queue.length}개 대기 중`);
            }
        });
    }

    // 큐 처리
    async processQueue() {
        if (this.processing || this.queue.length === 0) {
            return;
        }

        this.processing = true;

        const item = this.queue[0];

        try {
            if (this.debug) console.log(`[BLEQueue] 명령어 실행 시작: ${item.name}`);

            // 명령어 실행 (함수 형태로 전달됨)
            const result = await item.command();

            if (this.debug) console.log(`[BLEQueue] 명령어 실행 완료: ${item.name}`);

            item.resolve(result);
        } catch (error) {
            if (this.debug) console.error(`[BLEQueue] 명령어 실행 오류: ${item.name}`, error);
            item.reject(error);
        } finally {
            // 처리 완료된 항목 제거
            this.queue.shift();
            this.processing = false;

            // 큐에 대기 중인 항목이 있으면 계속 처리
            if (this.queue.length > 0) {
                // 10ms 지연 후 다음 명령 처리 (GATT 스택이 정리될 시간 확보)
                setTimeout(() => this.processQueue(), 10);

                if (this.debug) console.log(`[BLEQueue] 다음 명령 처리 대기 (10ms)`);
            } else if (this.debug) {
                console.log(`[BLEQueue] 모든 명령 처리 완료`);
            }
        }
    }
}

/**
 * BLE 코어 기능을 제공하는 클래스
 * 기존 BleLib 객체의 기능을 클래스화
 */
class BLECore {
    constructor() {
        // 상태 변수
        this.device = null;
        this.server = null;
        this.services = {};
        this.characteristics = {};
        this.isConnected = false;
        this.connectionInProgress = false;

        // 모드 관련 변수
        this.currentMode = null; // 'REPL' 또는 'IOT'
        this.modeSwitchInProgress = false;

        // 콜백 및 이벤트 관리
        this.notificationCallbacks = {}; // 특성별 알림 콜백 저장
        this.eventHandlers = {};        // 이벤트 핸들러 저장

        // 이벤트 콜백
        this.callbacks = {
            onConnected: null,
            onDisconnected: null,
            onConnectionFailed: null,
            onServiceReady: null,
            onConnectionChange: null,  // 연결 상태 변경 콜백 추가
            onDataReceived: null,       // 데이터 수신 콜백 추가
            onCameraData: null,
            onTouchData: null,
            onLightData: null,
            onData: null,
            onLedData: null,
            onUltrasonicData: null,
            onDhtData: null,
            onServoData: null,
            onNeopixelData: null,
            onBuzzerData: null,
            onReplData: null,          // REPL 모드 전환 데이터 콜백 추가
            onModeDetected: null,      // 모드 감지 콜백
            onModeSwitchStarted: null, // 모드 전환 시작 콜백
            onModeSwitchCompleted: null // 모드 전환 완료 콜백
        };

        // 명령어 큐 추가
        this.commandQueue = new BLECommandQueue();
    }

    /**
     * BLE 라이브러리 초기화
     * @param {Object} options - 초기화 옵션
     */
    init(options = {}) {
        // 옵션으로 콜백 설정
        if (options.onConnected) this.callbacks.onConnected = options.onConnected;
        if (options.onDisconnected) this.callbacks.onDisconnected = options.onDisconnected;
        if (options.onConnectionFailed) this.callbacks.onConnectionFailed = options.onConnectionFailed;
        if (options.onServiceReady) this.callbacks.onServiceReady = options.onServiceReady;

        console.log("BLE Library initialized");
    }

    /**
     * 연결 상태 변경 콜백 등록
     * @param {Function} callback - 연결 상태 변경시 호출될 콜백
     */
    onConnectionChange(callback) {
        this.callbacks.onConnectionChange = callback;
        // 현재 연결 상태 즉시 알림
        if (callback) {
            callback(this.isConnected);
        }
    }

    /**
     * 데이터 수신 콜백 등록
     * @param {Function} callback - 데이터 수신시 호출될 콜백
     */
    onDataReceived(callback) {
        console.log("[BLECore] 데이터 수신 콜백 등록됨");
        this.callbacks.onDataReceived = callback;
    }

    /**
     * 중앙 데이터 처리 함수
     * @param {string} characteristicUUID - 특성 UUID
     * @param {*} data - 수신 데이터
     * @returns {boolean} - 처리 여부
     */
    processReceivedData(characteristicUUID, data) {
        console.log(`[BLECore] 중앙 데이터 처리: (${characteristicUUID}):`, data);

        // 콜백이 등록되어 있으면 호출
        if (this.callbacks.onDataReceived) {
            const dataObj = {
                characteristicUUID: characteristicUUID,
                data: data
            };

            try {
                console.log("[BLECore] 콜백 함수 호출");
                this.callbacks.onDataReceived(dataObj);
                console.log("[BLECore] 콜백 함수 호출 완료");
            } catch (error) {
                console.error("[BLECore] 콜백 함수 호출 중 오류:", error);
            }
            return true;
        } else {
            console.log("[BLECore] 등록된 콜백 없음 - 직접 처리");
            return false;
        }
    }

    /**
     * 큐를 통한 명령어 전송
     * @param {string} characteristicUUID - 명령어를 전송할 특성의 UUID
     * @param {string} command - 전송할 명령어
     * @returns {Promise<boolean>} - 명령어 전송 성공 여부
     */
    async queueCommand(characteristicUUID, command) {
        console.log(`[BLECore] 큐를 통한 명령어 전송: ${command} (특성: ${characteristicUUID})`);

        // 명령어 실행 함수를 큐에 추가
        return this.commandQueue.enqueue(async () => {
            return await this.sendCommand(characteristicUUID, command);
        });
    }

    /**
     * 명령어를 특정 특성에 전송합니다.
     * @param {string} characteristicUUID - 명령어를 전송할 특성의 UUID
     * @param {string} command - 전송할 명령어
     * @returns {Promise<boolean>} - 명령어 전송 성공 여부
     */
    async sendCommand(characteristicUUID, command) {
        if (!this.isConnected) {
            console.error('[BLECore:DEBUG] 장치가 연결되어 있지 않아 명령을 전송할 수 없습니다.');
            throw new Error('장치가 연결되어 있지 않습니다. 먼저 연결해주세요.');
        }

        if (!this.server) {
            console.error('[BLECore:DEBUG] GATT 서버가 없습니다.');
            throw new Error('GATT 서버 연결이 없습니다. 먼저 연결해주세요.');
        }

        console.log(`[BLECore:DEBUG] 명령어 전송: ${command} (특성: ${characteristicUUID})`);

        try {
            // 특성 UUID에 맞는 서비스 UUID 결정
            const serviceUUID = this._getServiceUUIDForCharacteristic(characteristicUUID);
            console.log(`[BLECore:DEBUG] 서비스 선택: ${serviceUUID}`);

            // 해당 서비스가 초기화되었는지 확인
            if (!this.services[serviceUUID === IOT_SERVICE ? 'iotService' :
                serviceUUID === SENSOR_SERVICE ? 'sensorService' : 'replService']) {
                console.warn(`[BLECore:DEBUG] 서비스(${serviceUUID})가 아직 초기화되지 않았습니다. 서비스 초기화 시도...`);

                try {
                    // 서비스 가져오기 시도
                    const service = await this.server.getPrimaryService(serviceUUID);

                    // 서비스 캐싱
                    if (serviceUUID === IOT_SERVICE) {
                        this.services.iotService = service;
                    } else if (serviceUUID === SENSOR_SERVICE) {
                        this.services.sensorService = service;
                    } else if (serviceUUID === REPL_SERVICE) {
                        this.services.replService = service;
                    }

                    console.log(`[BLECore:DEBUG] 서비스(${serviceUUID}) 가져오기 성공`);
                } catch (error) {
                    console.error(`[BLECore:DEBUG] 서비스(${serviceUUID}) 가져오기 실패:`, error);
                    throw new Error(`서비스(${serviceUUID})를 찾을 수 없습니다: ${error.message}`);
                }
            }

            // 명령어 인코딩 및 전송
            const encoder = new TextEncoder();
            const commandBuffer = encoder.encode(command);

            // 특성에 명령어 쓰기
            await this.server.getPrimaryService(serviceUUID)
                .then(service => service.getCharacteristic(characteristicUUID))
                .then(characteristic => characteristic.writeValue(commandBuffer));

            console.log(`[BLECore:DEBUG] 명령어 전송 성공: ${command}`);
            return true;
        } catch (error) {
            console.error(`[BLECore:DEBUG] 명령어 전송 실패: ${error.message}`);
            throw new Error(`명령어 전송 실패: ${error.message}`);
        }
    }


    /**
     * 서비스 초기화 (내부용)
     * @returns {Promise<boolean>} - 초기화 성공 여부
     */
    async _initServices() {
        try {
            // 서비스 초기화
            this.services = {}; // 기존 서비스 정보 초기화
            this.characteristics = {}; // 기존 캐릭터리스틱 정보 초기화

            // IoT 모드 서비스 초기화
            console.log("Initializing IoT services");

            try {
                this.services.iotService = await this.server.getPrimaryService(IOT_SERVICE);
                console.log("IoT 서비스 초기화 성공");
            } catch (error) {
                console.warn("IoT 서비스를 찾을 수 없습니다:", error.message);
                // 서비스를 찾지 못해도 계속 진행
            }

            try {
                this.services.sensorService = await this.server.getPrimaryService(SENSOR_SERVICE);
                console.log("센서 서비스 초기화 성공");
            } catch (error) {
                console.warn("센서 서비스를 찾을 수 없습니다:", error.message);
                // 서비스를 찾지 못해도 계속 진행
            }

            // 최소한 하나의 서비스라도 초기화되었는지 확인
            if (!this.services.iotService && !this.services.sensorService) {
                console.error("필수 서비스를 찾을 수 없습니다");
                // 서비스가 하나도 없으면 경고만 하고 진행
            }

            // 서비스 준비 완료 콜백
            if (this.callbacks.onServiceReady) {
                this.callbacks.onServiceReady(this.services);
            }

            return true;
        } catch (err) {
            console.error("Error initializing services:", err);
            // 오류가 발생해도 연결 상태는 유지하고 true 반환
            return true;
        }
    }

    /**
     * BLE 장치 연결
     * @param {Array<string>} requiredServices - 추가로 필요한 서비스 UUID 배열
     * @returns {Promise<BluetoothRemoteGATTServer|undefined>} - GATT 서버 객체
     */
    async connect(requiredServices = []) {
        if (this.connectionInProgress) {
            console.log("Connection already in progress, ignoring request");
            return;
        }

        this.connectionInProgress = true;

        try {
            // IoT와 REPL 모드의 모든 서비스 UUID 추가
            const services = [
                IOT_SERVICE,
                SENSOR_SERVICE,
                REPL_SERVICE,
                ...requiredServices
            ];
            
            // 디바이스 검색
            // data-bluetoothname 속성을 가진 요소 및 값 확인
            const bluetoothNameElement = document.querySelector('[data-bluetoothname]');
            const hasCustomName = bluetoothNameElement && bluetoothNameElement.dataset.bluetoothname;
            
            if (hasCustomName) {
                this.device = await navigator.bluetooth.requestDevice({
                    filters: [
                        { namePrefix: bluetoothNameElement.dataset.bluetoothname }
                    ],
                    optionalServices: services
                });
            } else {
                this.device = await navigator.bluetooth.requestDevice({
                    filters: [
                        { namePrefix: 'DeepCoB' },
                        { namePrefix: 'DCB' }
                    ],
                    optionalServices: services
                });
            }
            
            
            

            // GATT 연결
            this.server = await this.device.gatt.connect();
            console.log(`Connected to: ${this.device.name}`);

            this.isConnected = true;

            // 장치 연결 해제 이벤트 리스너 등록
            this.device.addEventListener('gattserverdisconnected', this._handleDisconnection.bind(this));

            // 현재 모드 감지 (IoT 또는 REPL)
            await this._detectCurrentMode();

            // REPL 모드일 경우 IoT 모드로 전환
            if (this.currentMode === 'REPL') {
                console.log("Detected REPL mode, switching to IoT mode...");

                if (this.callbacks.onModeSwitchStarted) {
                    this.callbacks.onModeSwitchStarted('REPL', 'IoT');
                }

                // IoT 모드로 전환 시도
                await this._switchToIoTMode();

                this.connectionInProgress = false;
                return;
            }

            // IoT 모드일 경우 서비스 초기화 진행
            console.log("IoT mode detected, initializing services...");
            await this._initServices();

            // 연결 성공 콜백
            if (this.callbacks.onConnected) {
                this.callbacks.onConnected(this.device);
            }

            // 연결 상태 변경 콜백 호출
            if (this.callbacks.onConnectionChange) {
                this.callbacks.onConnectionChange(true);
            }

            this.connectionInProgress = false;
            return this.server;
        } catch (err) {
            console.error("Connection error:", err);

            // 상세 오류 메시지
            let errorMessage = "Connection failed";
            if (err.message) {
                errorMessage += `: ${err.message}`;
            }

            // 연결 실패 콜백
            if (this.callbacks.onConnectionFailed) {
                this.callbacks.onConnectionFailed(errorMessage);
            }

            this.isConnected = false;

            // 연결 상태 변경 콜백 호출
            if (this.callbacks.onConnectionChange) {
                this.callbacks.onConnectionChange(false);
            }

            this.connectionInProgress = false;
            throw err;
        }
    }

    /**
     * BLE 장치 연결 해제
     */
    disconnect() {
        if (this.device && this.device.gatt.connected) {
            this.device.gatt.disconnect();
            this.isConnected = false;
            console.log("Disconnected manually.");

            // 연결 해제 콜백
            if (this.callbacks.onDisconnected) {
                this.callbacks.onDisconnected('disconnected', 'Manually disconnected');
            }

            // 연결 상태 변경 콜백 호출
            if (this.callbacks.onConnectionChange) {
                this.callbacks.onConnectionChange(false);
            }
        }
    }

    /**
     * 장치 연결 해제 이벤트 핸들러
     * @param {Event} event - 이벤트 객체
     */
    _handleDisconnection(event) {
        if (!this.isConnected) return; // 이미 연결이 해제된 상태면 처리하지 않음

        console.log("장치 연결이 해제되었습니다.");
        this.isConnected = false;

        // 연결 해제 콜백 실행
        if (this.callbacks.onDisconnected) {
            this.callbacks.onDisconnected('disconnected', '장치 연결이 해제되었습니다');
        }

        // 연결 상태 변경 콜백 호출
        if (this.callbacks.onConnectionChange) {
            this.callbacks.onConnectionChange(false);
        }
    }

    /**
     * 현재 연결된 장치의 모드 감지 (IoT 또는 REPL)
     * @returns {Promise<string>} - 감지된 모드 (BOARD_MODE.IOT 또는 BOARD_MODE.REPL)
     */
    async _detectCurrentMode() {
        console.log("장치 모드 감지 중...");

        try {
            // 기본값으로 IoT 모드 가정
            this.currentMode = BOARD_MODE.IOT;

            // 실제 프로덕션에서는 모드 감지를 위한 로직 구현 필요
            // 단순화를 위해 항상 IoT 모드로 설정
            console.log(`장치 모드 감지 완료: ${this.currentMode}`);

            return this.currentMode;
        } catch (err) {
            console.error("모드 감지 중 오류:", err);
            // 오류 발생 시 기본값으로 IoT 모드 사용
            this.currentMode = BOARD_MODE.IOT;
            return this.currentMode;
        }
    }

    /**
     * 장치를 IoT 모드로 전환
     * @returns {Promise<boolean>} - 전환 성공 여부
     */
    async _switchToIoTMode() {
        console.log("IoT 모드로 전환 중...");

        try {
            // 이미 IoT 모드면 아무 작업도 수행하지 않음
            if (this.currentMode === BOARD_MODE.IOT) {
                console.log("이미 IoT 모드입니다.");
                return true;
            }

            this.modeSwitchInProgress = true;

            // 실제 프로덕션에서는 모드 전환을 위한 명령 전송 구현 필요
            // 여기서는 단순히 모드 변수만 변경

            // 전환 완료 처리
            this.currentMode = BOARD_MODE.IOT;
            this.modeSwitchInProgress = false;

            console.log("IoT 모드로 전환 완료");

            return true;
        } catch (err) {
            console.error("IoT 모드 전환 중 오류:", err);
            this.modeSwitchInProgress = false;
            return false;
        }
    }

    /**
     * 캐릭터리스틱의 UUID에 따라 서비스 UUID 판별
     * @param {string} characteristicUUID - 특성 UUID
     * @returns {string} - 서비스 UUID
     */
    _getServiceUUIDForCharacteristic(characteristicUUID) {
        // 기본적으로 IOT_SERVICE 사용
        let serviceUUID = IOT_SERVICE;

        // REPL 관련 특성이면 REPL_SERVICE 사용
        if (characteristicUUID === REPL_TX_CHARACTERISTIC ||
            characteristicUUID === REPL_RX_CHARACTERISTIC ||
            characteristicUUID === REPL_CONTROL_CHARACTERISTIC) {
            serviceUUID = REPL_SERVICE;
        }

        // 특정 캐릭터리스틱 UUID가 SENSOR_SERVICE에 속하는지 확인
        const sensor_characteristics = [
            ULTRA_CHARACTERISTIC,
            DHT_CHARACTERISTIC,
            SERVO_CHARACTERISTIC,
            NEOPIXEL_CHARACTERISTIC,
            TOUCH_CHARACTERISTIC,
            LIGHT_CHARACTERISTIC,
            BUZZER_CHARACTERISTIC,
            GYRO_CHARACTERISTIC,
            DUST_CHARACTERISTIC,
            DCMOTOR_CHARACTERISTIC,
            HEART_CHARACTERISTIC,
            EZ_LASER_CHARACTERISTIC,
            EZ_GYRO_CHARACTERISTIC,
            EZ_PRESS_CHARACTERISTIC,
            EZ_CO2_CHARACTERISTIC,
            EZ_DIYA_CHARACTERISTIC,
            EZ_DIYB_CHARACTERISTIC,
            EZ_HALL_CHARACTERISTIC,
            EZ_LCD_CHARACTERISTIC,
            EZ_LIGHT_CHARACTERISTIC,
            EZ_VOLT_CHARACTERISTIC,
            EZ_CURR_CHARACTERISTIC,
            EZ_HUMAN_CHARACTERISTIC,
            EZ_THERMAL_CHARACTERISTIC,
            EZ_SOUND_CHARACTERISTIC,
            EZ_WEIGHT_CHARACTERISTIC,
            EZ_DUST_CHARACTERISTIC
        ];

        if (sensor_characteristics.includes(characteristicUUID)) {
            serviceUUID = SENSOR_SERVICE;
        }

        console.log(`[BLECore:DEBUG] UUID ${characteristicUUID}에 대한 서비스 판별 결과: ${serviceUUID}`);
        return serviceUUID;
    }
}

/**
 * BLE 연결 관리자 클래스
 * BLECore를 상속하고 연결 관리 기능 추가
 */
class BLEManager extends BLECore {
    constructor() {
        super();

        // 추가적인 콜백 배열 (이벤트 처리용)
        this.onConnectedCallbacks = [];
        this.onDisconnectedCallbacks = [];
        this.onConnectionFailedCallbacks = [];

        // BLECore의 콜백을 자체 콜백과 연결
        this._setupCallbacks();

        // 싱글톤 패턴 적용
        if (BLEManager._instance) {
            return BLEManager._instance;
        }

        BLEManager._instance = this;
    }

    /**
     * 싱글톤 인스턴스 가져오기
     * @returns {BLEManager} - BLEManager 인스턴스
     */
    static getInstance() {
        if (!BLEManager._instance) {
            BLEManager._instance = new BLEManager();
        }
        return BLEManager._instance;
    }

    /**
     * BLECore 콜백과 자체 콜백 연결
     */
    _setupCallbacks() {
        // 연결 콜백 설정
        this.callbacks.onConnected = (device) => {
            this._triggerCallbacks('onConnected', device);
        };

        // 연결 해제 콜백 설정
        this.callbacks.onDisconnected = (reason, message) => {
            this._triggerCallbacks('onDisconnected', { reason, message });
        };

        // 연결 실패 콜백 설정
        this.callbacks.onConnectionFailed = (message) => {
            this._triggerCallbacks('onConnectionFailed', message);
        };
    }

    /**
     * 연결 성공 콜백 등록
     * @param {Function} callback - 연결 성공시 호출될 콜백
     * @returns {BLEManager} - 메서드 체이닝 지원
     */
    onConnected(callback) {
        if (typeof callback === 'function') {
            this.onConnectedCallbacks.push(callback);

            // 이미 연결되어 있는 경우 콜백 실행
            if (this.isConnected) {
                setTimeout(() => callback({ name: "이미 연결된 장치" }), 0);
            }
        }
        return this; // 메서드 체이닝 지원
    }

    /**
     * 연결 해제 콜백 등록
     * @param {Function} callback - 연결 해제시 호출될 콜백
     * @returns {BLEManager} - 메서드 체이닝 지원
     */
    onDisconnected(callback) {
        if (typeof callback === 'function') {
            this.onDisconnectedCallbacks.push(callback);
        }
        return this;
    }

    /**
     * 연결 실패 콜백 등록
     * @param {Function} callback - 연결 실패시 호출될 콜백
     * @returns {BLEManager} - 메서드 체이닝 지원
     */
    onConnectionFailed(callback) {
        if (typeof callback === 'function') {
            this.onConnectionFailedCallbacks.push(callback);
        }
        return this;
    }

    /**
     * 특성 알림 시작
     * @param {string} characteristicUUID - 알림을 시작할 특성 UUID
     * @param {Function} callback - 알림 받을 때 호출될 콜백
     * @returns {Promise<void>} - 알림 시작 프로미스
     */
    async startNotifications(characteristicUUID, callback) {
        EZ_LOG.info(`[BLEManager] ${characteristicUUID} 특성 알림 시작`);

        if (!this.isConnected || !this.server) {
            EZ_LOG.error(`[BLEManager] 장치가 연결되어 있지 않아 알림을 시작할 수 없습니다.`);
            throw new Error('장치가 연결되어 있지 않습니다.');
        }

        try {
            // 특성 UUID에 맞는 서비스 UUID 결정
            const serviceUUID = this._getServiceUUIDForCharacteristic(characteristicUUID);
            EZ_LOG.debug(`[BLEManager] 서비스 선택: ${serviceUUID}`);
            // 서비스 가져오기
            const service = await this.server.getPrimaryService(serviceUUID);
            // 특성 가져오기
            const char = await service.getCharacteristic(characteristicUUID);

            // 알림 수신 이벤트 리스너 먼저 등록
            const handleNotification = (event) => {
                const value = event.target.value;
                // 카메라/센서 스트리밍 등 고빈도 이벤트는 debug로만 로깅
                EZ_LOG.debug(`[BLEManager] 특성 알림 수신: ${characteristicUUID}`);
                if (callback) {
                    callback(value);
                }
            };
            char.addEventListener('characteristicvaluechanged', handleNotification);

            // 알림 시작
            setTimeout(() => {
                char.startNotifications();
            }, 1000);

            EZ_LOG.info(`[BLEManager] ${characteristicUUID} 특성 알림 시작 성공`);
            return Promise.resolve();
        } catch (error) {
            EZ_LOG.error(`[BLEManager] 특성 알림 시작 실패: ${error.message}`);
            throw error;
        }
    }

    /**
     * 콜백 실행
     * @param {string} type - 콜백 타입
     * @param {*} data - 콜백 데이터
     */
    _triggerCallbacks(type, data) {
        const callbacks = this[type + 'Callbacks'];
        if (callbacks && Array.isArray(callbacks)) {
            callbacks.forEach(callback => {
                try {
                    callback(data);
                } catch (error) {
                    console.error(`연결 이벤트 콜백 오류(${type}):`, error);
                }
            });
        }
    }
}

/**
 * 센서 기본 클래스
 * BLEManager 인스턴스를 사용하여 BLE 통신
 */
class SensorBase {
    /**
     * 센서 기본 클래스 생성자
     * @param {string} name - 센서 이름
     * @param {string} characteristicUUID - 센서 특성 UUID
     */
    constructor(name, characteristicUUID) {
        // super();

        this.name = name;
        this.characteristicUUID = characteristicUUID;

        // BLEManager 인스턴스 가져오기
        this.bleManager = BLEManager.getInstance();

        // 알림 설정
        this._setupNotifications();
    }

    /**
     * 특성 알림 설정
     */
    _setupNotifications() {
        // Console 디버깅
        EZ_LOG.debug(`[DEBUG] ${this.name} 센서의 _setupNotifications 호출됨`);
        EZ_LOG.debug(`[DEBUG] ${this.name} 특성 UUID: ${this.characteristicUUID}`);

        if (!this.bleManager) {
            EZ_LOG.error(`[DEBUG] ${this.name}: BLEManager 인스턴스가 없습니다`);
            return;
        }

        // 알림 지원 여부 확인 - LED, SERVO, NEOPIXEL은 알림을 지원하지 않음
        const notifyNotSupported = [
            LED_CHARACTERISTIC,
            DCMOTOR_CHARACTERISTIC,
            SERVO_CHARACTERISTIC,
            NEOPIXEL_CHARACTERISTIC,
            BUZZER_CHARACTERISTIC,
            EZ_LASER_CHARACTERISTIC  // 레이저 모듈도 알림을 필수로 사용하지 않음 (제어용)
        ];

        if (notifyNotSupported.includes(this.characteristicUUID)) {
            EZ_LOG.debug(`[DEBUG] ${this.name}: 이 센서(${this.characteristicUUID})는 알림을 지원하지 않습니다. 알림 설정 건너뜁니다.`);
            return;
        }

        // 연결 상태를 확인하고, 연결되지 않았으면 연결 후에 알림 설정
        if (!this.bleManager.isConnected) {
            EZ_LOG.debug(`[DEBUG] ${this.name}: 장치가 아직 연결되지 않았습니다. 연결 후 알림을 설정합니다.`);

            // 연결 완료 후 알림 설정을 위한 리스너 추가
            const self = this;
            this.bleManager.onConnected(function (device) {
                EZ_LOG.debug(`[DEBUG] ${self.name}: 장치 연결됨, 알림 설정 시도`);
                self._setupNotificationsAfterConnection();
            });

            return;
        }

        this._setupNotificationsAfterConnection();
    }

    /**
     * 연결 후 특성 알림 설정
     */
    _setupNotificationsAfterConnection() {
        // 명시적으로 특성 알림 구독
        const self = this;
        try {
            EZ_LOG.debug(`[DEBUG] ${this.name}: 특성 알림 시작 시도`);
            this.bleManager.startNotifications(this.characteristicUUID, function (data) {
                // 고빈도 데이터(카메라 청크 등)는 debug로만 출력
                EZ_LOG.debug(`[DEBUG] ${self.name} 알림 콜백 호출됨`);
                // 데이터 형식 일관성 유지
                self._processData({ data: data, characteristicUUID: self.characteristicUUID });
            }).then(() => {
                EZ_LOG.debug(`[DEBUG] ${self.name}: 특성 알림 시작 성공`);
            }).catch(error => {
                EZ_LOG.warn(`[DEBUG] ${self.name}: 특성 알림 시작 실패`);
            });

            // 기존 onDataReceived도 유지
            this.bleManager.onDataReceived(function (data) {
                if (data.characteristicUUID === self.characteristicUUID) {
                    EZ_LOG.debug(`[DEBUG] ${self.name} onDataReceived 콜백 호출됨`);
                    self._processData(data); // 데이터 형식 일관성 유지
                }
            });
        } catch (error) {
            EZ_LOG.error(`[DEBUG] ${this.name}: 알림 설정 중 오류`);
        }
    }

    /**
     * 명령어 전송 - 큐 시스템을 통한 전송으로 변경
     * @param {string} command - 전송할 명령어
     * @returns {Promise<boolean>} - 전송 성공 여부
     */
    async sendCommand(command) {
        if (!this.bleManager) {
            const error = new Error(`[${this.name}] BLEManager 인스턴스가 없습니다`);
            console.error(error.message);
            throw error;
        }

        try {
            // 큐 시스템을 통해 명령어 전송 (직접 sendCommand 호출 대신)
            return await this.bleManager.queueCommand(this.characteristicUUID, command);
        } catch (error) {
            console.error(`[${this.name}] 명령어(${command}) 전송 오류: ${error.message}`);
            throw error;
        }
    }

    /**
     * 데이터 처리 (하위 클래스에서 구현)
     * @param {*} data - 수신 데이터
     */
    _processData(data) {
        // 하위 클래스에서 구현
    }
}

/**
 * LED 센서 클래스
 * SensorBase 상속
 */
class LED extends SensorBase {
    /**
     * LED 센서 클래스 생성자
     */
    constructor() {
        super('LED', LED_CHARACTERISTIC);
        this.state = "unknown"; // LED 상태 추적
    }

    /**
     * 현재 LED 상태 반환
     * @returns {string} - LED 상태 (on/off/blink/unknown)
     */
    getState() {
        return this.state;
    }

    /**
     * LED 켜기
     * @returns {Promise<boolean>} - 성공 여부
     */
    async turnOn() {
        try {
            const result = await this.sendCommand("LED:ON");
            if (result) this.state = "on";
            return result;
        } catch (error) {
            console.error(`[LED] 켜기 오류: ${error.message}`);
            throw error;
        }
    }

    /**
     * LED 끄기
     * @returns {Promise<boolean>} - 성공 여부
     */
    async turnOff() {
        try {
            const result = await this.sendCommand("LED:OFF");
            if (result) this.state = "off";
            return result;
        } catch (error) {
            console.error(`[LED] 끄기 오류: ${error.message}`);
            throw error;
        }
    }

    /**
     * LED 깜빡이기
     * @param {number} interval - 깜빡임 간격 (ms)
     * @returns {Promise<boolean>} - 성공 여부
     */
    async blink(interval = 1000) {
        try {
            const result = await this.sendCommand(`LED:BLINK:${interval}`);
            if (result) this.state = "blink";
            return result;
        } catch (error) {
            console.error(`[LED] 깜빡이기 오류: ${error.message}`);
            throw error;
        }
    }

    /**
     * LED 밝기 설정
     * @param {number} brightness - 밝기 (0-100)
     * @returns {Promise<boolean>} - 성공 여부
     */
    async setBrightness(brightness) {
        if (brightness < 0) brightness = 0;
        if (brightness > 100) brightness = 100;

        try {
            return await this.sendCommand(`LED:BRIGHTNESS:${brightness}`);
        } catch (error) {
            console.error(`[LED] 밝기 설정 오류: ${error.message}`);
            throw error;
        }
    }

    /**
     * LED 핀 설정
     * @param {number} pin - 핀 번호
     * @returns {Promise<boolean>} - 성공 여부
     */
    async setPin(pin) {
        return await this.sendCommand(`LED:PIN:${pin}`);
    }

    /**
     * LED 데이터 처리
     * @param {*} data - 수신 데이터
     */
    _processData(data) {
        if (!data) return;

        const dataStr = data.toString();

        // LED 데이터 파싱
        const parsedData = {
            raw: dataStr,
            success: dataStr.includes(":OK"),
            state: dataStr.includes("LED:ON") ? "on" :
                dataStr.includes("LED:OFF") ? "off" :
                    dataStr.includes("LED:BLINK") ? "blink" : "unknown"
        };

        // 상태 업데이트
        if (parsedData.state !== "unknown") {
            this.state = parsedData.state;
        }
    }
}

/**
 * 레이저 모듈 클래스 (EZMaker 전용)
 * SensorBase 상속
 */
class Laser extends SensorBase {
    /**
     * 레이저 모듈 클래스 생성자
     */
    constructor() {
        super('Laser', LASER_CHARACTERISTIC);
        this.state = "unknown"; // 레이저 상태 추적 (on/off)
    }

    /**
     * 현재 레이저 상태 반환
     * @returns {string} - 레이저 상태 (on/off/unknown)
     */
    getState() {
        return this.state;
    }

    /**
     * 레이저 켜기
     * @returns {Promise<boolean>} - 성공 여부
     */
    async turnOn() {
        try {
            const result = await this.sendCommand("LASER:ON");
            if (result) this.state = "on";
            return result;
        } catch (error) {
            console.error(`[Laser] 켜기 오류: ${error.message}`);
            throw error;
        }
    }

    /**
     * 레이저 끄기
     * @returns {Promise<boolean>} - 성공 여부
     */
    async turnOff() {
        try {
            const result = await this.sendCommand("LASER:OFF");
            if (result) this.state = "off";
            return result;
        } catch (error) {
            console.error(`[Laser] 끄기 오류: ${error.message}`);
            throw error;
        }
    }

    /**
     * 레이저 모듈 핀 설정
     * @param {number} pin - 핀 번호 (예: EZMaker D0 → GPIO 21)
     * @returns {Promise<boolean>} - 성공 여부
     */
    async setPin(pin) {
        try {
            return await this.sendCommand(`LASER:PIN:${pin}`);
        } catch (error) {
            console.error(`[Laser] 핀 설정 오류: ${error.message}`);
            throw error;
        }
    }

    /**
     * 레이저 데이터 처리 (옵션)
     * @param {*} data - 수신 데이터
     */
    _processData(data) {
        if (!data) return;

        const dataStr = data.toString();

        const parsedData = {
            raw: dataStr,
            success: dataStr.includes("LASER:") && dataStr.includes(":OK"),
            state: dataStr.includes("LASER:ON") ? "on" :
                   dataStr.includes("LASER:OFF") ? "off" : this.state
        };

        this.state = parsedData.state;
    }
}

/**
 * 조도센서 클래스
 * SensorBase 상속
 */
class LightSensor extends SensorBase {
    constructor() {
        super('Light', LIGHT_CHARACTERISTIC);
        this.analog = null;    // 클래스 멤버 변수로 저장
        this.digital = null;   // 클래스 멤버 변수로 저장
    }

    /**
     * 아날로그 값 반환
     * @returns {number|null} - 아날로그 측정값 또는 null
     */
    getAnalog() {
        return this.analog;
    }

    /**
     * 디지털 값 반환
     * @returns {number|null} - 디지털 측정값 또는 null
     */
    getDigital() {
        return this.digital;
    }

    /**
     * 조도센서 상태 요청
     * @returns {Promise<boolean>} - 성공 여부
     */
    async getStatus() {
        console.log("조도센서 상태 요청 전송");
        return await this.sendCommand("LIGHT:STATUS");
    }

    /**
     * 조도센서 핀 설정
     * @param {number} analogPin - 아날로그 핀 번호
     * @param {number|null} digitalPin - 디지털 핀 번호
     * @returns {Promise<boolean>} - 성공 여부
     */
    async setPin(analogPin, digitalPin = null) {
        if (digitalPin !== null) {
            return await this.sendCommand(`LIGHT:PIN:${analogPin},${digitalPin}`);
        } else {
            return await this.sendCommand(`LIGHT:PIN:${analogPin}`);
        }
    }

    /**
     * 조도센서 데이터 처리
     * @param {*} data - 수신 데이터
     */
    _processData(data) {
        if (!data) return;

        console.log("[LightSensor] 데이터 수신 확인:", data);

        // 데이터 형식 확인 - data.data 구조 처리 추가
        let actualData = data;
        if (data && typeof data === 'object' && data.data !== undefined) {
            console.log("[LightSensor] data.data 구조 감지, 내부 데이터 사용");
            actualData = data.data;  // 중첩된 구조 처리
        }

        // 데이터 변환 시도
        let dataStr;
        try {
            // ArrayBuffer 또는 DataView인 경우 텍스트로 변환
            if (actualData instanceof ArrayBuffer) {
                const decoder = new TextDecoder('utf-8');
                dataStr = decoder.decode(new DataView(actualData));
                console.log("[LightSensor] ArrayBuffer에서 변환된 문자열:", dataStr);
            } else if (actualData instanceof DataView) {
                const decoder = new TextDecoder('utf-8');
                dataStr = decoder.decode(actualData);
                console.log("[LightSensor] DataView에서 변환된 문자열:", dataStr);
            } else if (actualData && actualData.buffer instanceof ArrayBuffer) {
                // TypedArray 처리 (Uint8Array 등)
                const decoder = new TextDecoder('utf-8');
                dataStr = decoder.decode(actualData);
                console.log("[LightSensor] TypedArray에서 변환된 문자열:", dataStr);
            } else {
                // 문자열이거나 다른 타입으로 안전하게 변환
                dataStr = String(actualData);
                console.log("[LightSensor] 기본 변환 문자열:", dataStr);
            }
        } catch (e) {
            console.error("[LightSensor] 데이터 변환 오류:", e);
            dataStr = String(actualData || "");
            console.log("[LightSensor] 오류 후 강제 변환 문자열:", dataStr);
        }

        // 조도센서 값 파싱 (여러 형식 지원)
        let analog = null, digital = null;

        try {
            // 1. "LIGHT:1234,1" 형식 처리
            if (dataStr.startsWith("LIGHT:") && dataStr.includes(",")) {
                const valueStr = dataStr.substring(6); // "LIGHT:" 제거
                const parts = valueStr.split(",");
                if (parts.length >= 2) {
                    analog = parseInt(parts[0]);
                    digital = parseInt(parts[1]);
                    console.log(`[LightSensor] 형식1 파싱: 아날로그=${analog}, 디지털=${digital}`);
                }
            }

            // 값이 유효한지 확인
            if (analog !== null || digital !== null) {
                // 클래스 멤버 변수에 저장
                this.analog = analog;
                this.digital = digital;
            } else {
                console.warn("[LightSensor] 조도센서 데이터 파싱 실패:", dataStr);
            }
        } catch (e) {
            console.error("[LightSensor] 조도센서 데이터 파싱 오류:", e);
        }
    }
}


/**
 * 센서에서 값을 가져오는 함수 (재시도 로직 포함)
 * @param {Object} sensor - 센서 객체 (getStatus, getAnalog 메소드 필요)
 * @param {number} maxRetries - 최대 재시도 횟수 (기본값: 3)
 * @param {number} retryDelay - 재시도 간격 (밀리초, 기본값: 50)
 * @returns {Promise<number|null>} 센서 값 또는 null
 */

function getLightSensorValue(sensor, maxRetries = 3, retryDelay = 50) {
    let retries = 0;

    function tryGetValue() {
        // 센서가 null이거나 undefined인 경우 처리
        if (!sensor) {
            console.log("센서 객체가 없습니다");
            return Promise.resolve(null);
        }

        return sensor.getStatus().then(() => {
            // getAnalog 메소드 존재 여부 확인
            if (typeof sensor.getAnalog === 'function') {
                const value = sensor.getAnalog();

                // 값이 null이거나 undefined이고 재시도 횟수가 남아있으면 재시도
                if ((value === null || value === undefined) && retries < maxRetries) {
                    retries++;
                    console.log(`센서 값이 null, 재시도 ${retries}/${maxRetries}`);

                    // 재시도를 위한 지연 및 재귀 호출
                    return new Promise(resolve => {
                        setTimeout(() => resolve(tryGetValue()), retryDelay);
                    });
                }

                // 유효한 값이나 최대 재시도 후 최종 값 반환
                return value;
            } else {
                console.log("센서에 getAnalog 메소드가 없습니다");
                return null;
            }
        });
    }

    // 실행 및 오류 처리
    return tryGetValue().catch((error) => {
        console.log("센서 데이터 요청 중 오류 발생:", error);
        return null;
    });
}

// 추가 헬퍼 함수 작성
async function getValidLightSensorValue(sensor) {
    const value = await getLightSensorValue(sensor);
    if (value === null || value === undefined) {
        throw new Error("유효한 센서 값이 없습니다");
    }
    return value;
}

/**
 * 초음파 센서 클래스
 * SensorBase 상속
 */
class UltrasonicSensor extends SensorBase {
    /**
     * 초음파 센서 클래스 생성자
     */
    constructor() {
        super('Ultrasonic', ULTRA_CHARACTERISTIC);
        this.distance = null; // 거리 값 저장용 멤버 변수 추가
    }

    /**
     * 현재 거리 값 반환
     * @returns {number|null} - 측정된 거리(cm) 또는 null
     */
    getDistance() {
        return this.distance;
    }

    /**
     * 거리 측정 요청
     * @returns {Promise<boolean>} - 성공 여부
     */
    async getStatus() {
        return await this.sendCommand("ULTRA:STATUS");
    }

    /**
     * 초음파 센서 핀 설정
     * @param {number} trigPin - 트리거 핀
     * @param {number} echoPin - 에코 핀
     * @returns {Promise<boolean>} - 성공 여부
     */
    async setPin(trigPin, echoPin) {
        return await this.sendCommand(`ULTRA:PIN:${trigPin},${echoPin}`);
    }

    /**
     * 초음파 센서 데이터 처리
     * @param {*} data - 수신 데이터
     */
    _processData(data) {
        if (!data) return;

        console.log("[UltrasonicSensor] 데이터 수신 확인:", data);

        // 데이터 형식 확인 - data.data 구조 처리 추가
        let actualData = data;
        if (data && typeof data === 'object' && data.data !== undefined) {
            console.log("[UltrasonicSensor] data.data 구조 감지, 내부 데이터 사용");
            actualData = data.data;  // 중첩된 구조 처리
        }

        // 데이터 변환 시도
        let dataStr;
        try {
            // ArrayBuffer 또는 DataView인 경우 텍스트로 변환
            if (actualData instanceof ArrayBuffer) {
                const decoder = new TextDecoder('utf-8');
                dataStr = decoder.decode(new DataView(actualData));
                console.log("[UltrasonicSensor] ArrayBuffer에서 변환된 문자열:", dataStr);
            } else if (actualData instanceof DataView) {
                const decoder = new TextDecoder('utf-8');
                dataStr = decoder.decode(actualData);
                console.log("[UltrasonicSensor] DataView에서 변환된 문자열:", dataStr);
            } else if (actualData && actualData.buffer instanceof ArrayBuffer) {
                // TypedArray 처리 (Uint8Array 등)
                const decoder = new TextDecoder('utf-8');
                dataStr = decoder.decode(actualData);
                console.log("[UltrasonicSensor] TypedArray에서 변환된 문자열:", dataStr);
            } else {
                // 문자열이거나 다른 타입으로 안전하게 변환
                dataStr = String(actualData);
                console.log("[UltrasonicSensor] 기본 변환 문자열:", dataStr);
            }
        } catch (e) {
            console.error("[UltrasonicSensor] 데이터 변환 오류:", e);
            dataStr = String(actualData || "");
            console.log("[UltrasonicSensor] 오류 후 강제 변환 문자열:", dataStr);
        }

        // ULTRA:거리값 형식 처리
        let distance = null;

        try {
            // "ULTRA:123.45" 형식 처리
            if (dataStr.startsWith("ULTRA:")) {
                const distanceStr = dataStr.replace("ULTRA:", "");
                distance = parseFloat(distanceStr);
                console.log(`[UltrasonicSensor] 파싱된 거리: ${distance}cm`);

                // 멤버 변수에 저장
                this.distance = distance;
            }

            // 값이 유효한지 확인
            if (distance !== null) {
                const parsedData = {
                    raw: dataStr,
                    distance: distance
                };

                console.log("[UltrasonicSensor] 초음파센서 파싱 완료:", parsedData);
            } else {
                console.warn("[UltrasonicSensor] 초음파센서 데이터 파싱 실패:", dataStr);
            }
        } catch (e) {
            console.error("[UltrasonicSensor] 초음파센서 데이터 파싱 오류:", e);
        }
    }
}

/**
 * 초음파 센서에서 거리 값을 가져오는 함수 (재시도 로직 포함)
 * @param {Object} sensor - 초음파 센서 객체 (getStatus, getDistance 메소드 필요)
 * @param {number} maxRetries - 최대 재시도 횟수 (기본값: 3)
 * @param {number} retryDelay - 재시도 간격 (밀리초, 기본값: 50)
 * @returns {Promise<number|null>} 거리 값(cm) 또는 null
 */

function getUltrasonicSensorValue(sensor, maxRetries = 3, retryDelay = 50) {
    let retries = 0;

    function tryGetValue() {
        // 센서가 null이거나 undefined인 경우 처리
        if (!sensor) {
            console.log("초음파 센서 객체가 없습니다");
            return Promise.resolve(null);
        }

        return sensor.getStatus().then(() => {
            // getDistance 메소드 존재 여부 확인
            if (typeof sensor.getDistance === 'function') {
                const distance = sensor.getDistance();

                // 값이 null이거나 undefined이고 재시도 횟수가 남아있으면 재시도
                if ((distance === null || distance === undefined) && retries < maxRetries) {
                    retries++;
                    console.log(`초음파 센서 값이 null, 재시도 ${retries}/${maxRetries}`);

                    // 재시도를 위한 지연 및 재귀 호출
                    return new Promise(resolve => {
                        setTimeout(() => resolve(tryGetValue()), retryDelay);
                    });
                }

                // 유효한 값이나 최대 재시도 후 최종 값 반환
                return distance;
            } else {
                console.log("초음파 센서에 getDistance 메소드가 없습니다");
                return null;
            }
        });
    }

    // 실행 및 오류 처리
    return tryGetValue().catch((error) => {
        console.log("초음파 센서 데이터 요청 중 오류 발생:", error);
        return null;
    });
}

/**
 * 초음파 센서에서 유효한 값을 가져오는 헬퍼 함수
 * @param {Object} sensor - 초음파 센서 객체
 * @returns {Promise<number>} - 유효한 거리 값(cm)
 * @throws {Error} - 유효한 값이 없을 경우 오류 발생
 */
async function getValidUltrasonicValue(sensor) {
    let distance = await getUltrasonicSensorValue(sensor);
    console.log(`[getValidUltrasonicValue] 초음파 센서 값: ${distance}`);
    if (distance === null || distance === undefined) {
        throw new Error("유효한 초음파 센서 값이 없습니다");
    }
    if (distance == 0 || distance == -0.0) {
        distance = 999;
        console.log("초음파 센서 값이 0입니다. 900으로 변경합니다.");
    }
    return distance;
}


/**
 * DHT 센서 클래스
 * SensorBase 상속
 */
class DHTSensor extends SensorBase {
    /**
     * DHT 센서 클래스 생성자
     */
    constructor() {
        super('DHT', DHT_CHARACTERISTIC);
        this.temperature = null; // 온도 저장용 멤버 변수
        this.humidity = null;    // 습도 저장용 멤버 변수
    }

    /**
     * 현재 온도 값 반환
     * @returns {number|null} - 측정된 온도(°C) 또는 null
     */
    getTemperature() {
        return this.temperature;
    }

    /**
     * 현재 습도 값 반환
     * @returns {number|null} - 측정된 습도(%) 또는 null
     */
    getHumidity() {
        return this.humidity;
    }

    /**
     * 온습도 측정 요청
     * @returns {Promise<boolean>} - 성공 여부
     */
    async getStatus() {
        return await this.sendCommand("DHT:STATUS");
    }

    /**
     * DHT 센서 핀 설정
     * @param {number} pin - 센서 핀
     * @returns {Promise<boolean>} - 성공 여부
     */
    async setPin(pin) {
        return await this.sendCommand(`DHT:PIN:${pin}`);
    }

    /**
     * DHT 센서 데이터 처리
     * @param {*} data - 수신 데이터
     */
    _processData(data) {
        if (!data) return;

        console.log("[DHTSensor] 데이터 수신 확인:", data);

        // 데이터 형식 확인 - data.data 구조 처리 추가
        let actualData = data;
        if (data && typeof data === 'object' && data.data !== undefined) {
            console.log("[DHTSensor] data.data 구조 감지, 내부 데이터 사용");
            actualData = data.data;  // 중첩된 구조 처리
        }

        // 데이터 변환 시도
        let dataStr;
        try {
            // ArrayBuffer 또는 DataView인 경우 텍스트로 변환
            if (actualData instanceof ArrayBuffer) {
                const decoder = new TextDecoder('utf-8');
                dataStr = decoder.decode(new DataView(actualData));
                console.log("[DHTSensor] ArrayBuffer에서 변환된 문자열:", dataStr);
            } else if (actualData instanceof DataView) {
                const decoder = new TextDecoder('utf-8');
                dataStr = decoder.decode(actualData);
                console.log("[DHTSensor] DataView에서 변환된 문자열:", dataStr);
            } else if (actualData && actualData.buffer instanceof ArrayBuffer) {
                // TypedArray 처리 (Uint8Array 등)
                const decoder = new TextDecoder('utf-8');
                dataStr = decoder.decode(actualData);
                console.log("[DHTSensor] TypedArray에서 변환된 문자열:", dataStr);
            } else {
                // 문자열이거나 다른 타입으로 안전하게 변환
                dataStr = String(actualData);
                console.log("[DHTSensor] 기본 변환 문자열:", dataStr);
            }
        } catch (e) {
            console.error("[DHTSensor] 데이터 변환 오류:", e);
            dataStr = String(actualData || "");
            console.log("[DHTSensor] 오류 후 강제 변환 문자열:", dataStr);
        }

        // DHT:T=온도,H=습도 형식 처리
        let temperature = null, humidity = null;

        try {
            // DHT:T=온도,H=습도 형식 처리
            if (dataStr.includes("T=") && dataStr.includes("H=")) {
                const tempMatch = dataStr.match(/T=([0-9.]+)/);
                const humidMatch = dataStr.match(/H=([0-9.]+)/);

                if (tempMatch && tempMatch.length > 1) {
                    temperature = parseFloat(tempMatch[1]);
                    this.temperature = temperature; // 멤버 변수에 저장
                    console.log(`[DHTSensor] 파싱된 온도: ${temperature}°C`);
                }

                if (humidMatch && humidMatch.length > 1) {
                    humidity = parseFloat(humidMatch[1]);
                    this.humidity = humidity; // 멤버 변수에 저장
                    console.log(`[DHTSensor] 파싱된 습도: ${humidity}%`);
                }
            }


        } catch (error) {
            console.error(`[DHTSensor] 데이터 파싱 오류: ${error.message}`);
        }
    }
}

/**
 * 온습도 센서에서 온도와 습도 값을 가져오는 함수 (재시도 로직 포함)
 * @param {Object} sensor - DHT 센서 객체 (getStatus, getTemperature, getHumidity 메소드 필요)
 * @param {number} maxRetries - 최대 재시도 횟수 (기본값: 3)
 * @param {number} retryDelay - 재시도 간격 (밀리초, 기본값: 50)
 * @returns {Promise<{temperature: number|null, humidity: number|null}|null>} 온도와 습도 값 객체 또는 null
 */
function getDHTSensorValue(sensor, maxRetries = 3, retryDelay = 50) {
    let retries = 0;

    function tryGetValue() {
        // 센서가 null이거나 undefined인 경우 처리
        if (!sensor) {
            console.log("온습도 센서 객체가 없습니다");
            return Promise.resolve(null);
        }

        return sensor.getStatus().then(() => {
            // 온도와 습도 메소드 존재 여부 확인
            const hasTemperature = typeof sensor.getTemperature === 'function';
            const hasHumidity = typeof sensor.getHumidity === 'function';

            if (!hasTemperature && !hasHumidity) {
                console.log("온습도 센서에 getTemperature 또는 getHumidity 메소드가 없습니다");
                return null;
            }

            // 온도와 습도 값 가져오기
            const temperature = hasTemperature ? sensor.getTemperature() : null;
            const humidity = hasHumidity ? sensor.getHumidity() : null;

            // 둘 다 null이고 재시도 횟수가 남아있으면 재시도
            if ((temperature === null && humidity === null) && retries < maxRetries) {
                retries++;
                console.log(`온습도 센서 값이 null, 재시도 ${retries}/${maxRetries}`);

                // 재시도를 위한 지연 및 재귀 호출
                return new Promise(resolve => {
                    setTimeout(() => resolve(tryGetValue()), retryDelay);
                });
            }

            // 유효한 값이나 최대 재시도 후 최종 값 반환
            return { temperature, humidity };
        });
    }

    // 실행 및 오류 처리
    return tryGetValue().catch((error) => {
        console.log("온습도 센서 데이터 요청 중 오류 발생:", error);
        return null;
    });
}

/**
 * 온습도 센서에서 유효한 값을 가져오는 헬퍼 함수
 * @param {Object} sensor - DHT 센서 객체
 * @returns {Promise<{temperature: number, humidity: number}>} - 유효한 온도와 습도 값
 * @throws {Error} - 유효한 값이 없을 경우 오류 발생
 */
async function getValidDHTValue(sensor) {
    const result = await getDHTSensorValue(sensor);
    if (!result) {
        throw new Error("온습도 센서 값을 가져올 수 없습니다");
    }

    // 온도와 습도 중 하나라도 유효한 값이 있는지 확인
    const hasValidTemp = result.temperature !== null && result.temperature !== undefined;
    const hasValidHumid = result.humidity !== null && result.humidity !== undefined;

    if (!hasValidTemp && !hasValidHumid) {
        throw new Error("유효한 온도 및 습도 값이 없습니다");
    }

    // 유효한 값만 포함한 객체 반환 (없는 값은 null로 유지)
    return {
        temperature: hasValidTemp ? result.temperature : null,
        humidity: hasValidHumid ? result.humidity : null
    };
}


/**
 * 터치 센서 클래스
 * SensorBase 상속
 */
class TouchSensor extends SensorBase {
    /**
     * 터치 센서 클래스 생성자
     */
    constructor() {
        super('Touch', TOUCH_CHARACTERISTIC);
        this.touched = false; // 터치 상태 저장용 멤버 변수
    }

    /**
     * 현재 터치 상태 반환
     * @returns {boolean} - 터치됨(true) 또는 터치 안됨(false)
     */
    isTouched() {
        return this.touched;
    }

    /**
     * 터치 상태 요청
     * @returns {Promise<boolean>} - 성공 여부
     */
    async getStatus() {
        return await this.sendCommand("TOUCH:STATUS");
    }

    /**
     * 터치 센서 핀 설정
     * @param {number} pin - 센서 핀
     * @returns {Promise<boolean>} - 성공 여부
     */
    async setPin(pin) {
        return await this.sendCommand(`TOUCH:PIN:${pin}`);
    }

    /**
     * 터치 센서 데이터 처리
     * @param {*} data - 수신 데이터
     */
    _processData(data) {
        if (!data) return;

        console.log("[TouchSensor] 데이터 수신 확인:", data);

        let actualData = data;
        if (data && typeof data === 'object' && data.data !== undefined) {
            console.log("[TouchSensor] data.data 구조 감지, 내부 데이터 사용");
            actualData = data.data;
        }

        let dataStr;
        try {
            if (actualData instanceof ArrayBuffer) {
                const decoder = new TextDecoder('utf-8');
                dataStr = decoder.decode(new DataView(actualData));
            } else if (actualData instanceof DataView) {
                const decoder = new TextDecoder('utf-8');
                dataStr = decoder.decode(actualData);
            } else if (actualData && actualData.buffer instanceof ArrayBuffer) {
                const decoder = new TextDecoder('utf-8');
                dataStr = decoder.decode(actualData);
            } else {
                dataStr = String(actualData);
            }
        } catch (e) {
            console.error("[TouchSensor] 데이터 변환 오류:", e);
            dataStr = String(actualData || "");
        }

        // TOUCH:1 또는 TOUCH:0 형식 처리
        let touched = false;
        if (dataStr.includes("TOUCH:1")) {
            touched = true;
        }

        this.touched = touched;
        console.log(`[TouchSensor] 파싱 결과: touched=${this.touched}`);
    }
}

/**
 * EZMaker 인체감지 센서 클래스 (HUMAN)
 * SensorBase 상속, EZ_HUMAN_CHARACTERISTIC 사용
 */
class HumanSensor extends SensorBase {
    /**
     * 인체감지 센서 생성자
     */
    constructor() {
        super('Human', EZ_HUMAN_CHARACTERISTIC);
        this.value = 0; // 0: 감지 없음, 1: 인체 감지
    }

    /**
     * 현재 감지 값(0 또는 1) 반환
     * @returns {number}
     */
    getValue() {
        return this.value;
    }

    /**
     * 인체 감지 여부 반환
     * @returns {boolean}
     */
    isDetected() {
        return this.value === 1;
    }

    /**
     * 인체감지 센서 상태 요청
     * @returns {Promise<boolean>}
     */
    async getStatus() {
        return await this.sendCommand("HUMAN:STATUS");
    }

    /**
     * 인체감지 센서 핀 설정
     * @param {number} pin - 센서가 연결된 디지털 핀 번호
     * @returns {Promise<boolean>}
     */
    async setPin(pin) {
        return await this.sendCommand(`HUMAN:PIN:${pin}`);
    }

    /**
     * 인체감지 센서 데이터 처리
     * @param {*} data - 수신 데이터
     */
    _processData(data) {
        if (!data) return;

        console.log("[HumanSensor] 데이터 수신 확인:", data);

        let actualData = data;
        if (data && typeof data === 'object' && data.data !== undefined) {
            console.log("[HumanSensor] data.data 구조 감지, 내부 데이터 사용");
            actualData = data.data;
        }

        let dataStr;
        try {
            if (actualData instanceof ArrayBuffer) {
                const decoder = new TextDecoder('utf-8');
                dataStr = decoder.decode(new DataView(actualData));
            } else if (actualData instanceof DataView) {
                const decoder = new TextDecoder('utf-8');
                dataStr = decoder.decode(actualData);
            } else if (actualData && actualData.buffer instanceof ArrayBuffer) {
                const decoder = new TextDecoder('utf-8');
                dataStr = decoder.decode(actualData);
            } else {
                dataStr = String(actualData);
            }
        } catch (e) {
        console.error("[HumanSensor] 데이터 변환 오류:", e);
            dataStr = String(actualData || "");
        }

        // HUMAN:0 또는 HUMAN:1 형식 처리
        if (dataStr.startsWith("HUMAN:")) {
            const valStr = dataStr.substring(6);
            const v = parseInt(valStr, 10);
            if (!isNaN(v)) {
                this.value = v ? 1 : 0;
                console.log(`[HumanSensor] 파싱 결과: value=${this.value}`);
            }
        }
    }
}

/**
 * 서보모터 클래스
 * SensorBase 상속
 */
class ServoMotor extends SensorBase {
    /**
     * 서보모터 클래스 생성자
     */
    constructor() {
        super('Servo', SERVO_CHARACTERISTIC);
        this.currentAngle = 0; // 첫 번째 서보 현재 각도
        this.currentAngle2 = 0; // 두 번째 서보 현재 각도
    }

    /**
     * 현재 서보 각도 반환 (첫 번째 서보)
     * @returns {number} - 현재 설정된 각도(0-180)
     */
    getAngle() {
        return this.currentAngle;
    }

    /**
     * 두 번째 서보 각도 반환
     * @returns {number} - 현재 설정된 각도(0-180)
     */
    getAngle2() {
        return this.currentAngle2;
    }

    /**
     * 특정 서보의 각도 반환
     * @param {number} index - 서보 인덱스 (1 또는 2)
     * @returns {number} - 현재 설정된 각도(0-180)
     */
    getAngleByIndex(index) {
        if (index === 2) {
            return this.currentAngle2;
        }
        return this.currentAngle; // 기본값 또는 잘못된 인덱스는 첫 번째 서보 값 반환
    }

    /**
     * 서보 각도 설정 (첫 번째 서보)
     * @param {number} angle - 각도 (0-180)
     * @returns {Promise<boolean>} - 성공 여부
     */
    async setAngle(angle) {
        if (angle < 0) angle = 0;
        if (angle > 180) angle = 180;

        try {
            // 성공시에만 현재 각도 업데이트
            const result = await this.sendCommand(`SERVO:${angle}`);
            if (result) {
                this.currentAngle = angle;
            }
            return result;
        } catch (error) {
            console.error(`[ServoMotor] 각도 설정 오류: ${error.message}`);
            throw error;
        }
    }
    
    /**
     * 두 번째 서보 각도 설정
     * @param {number} angle - 각도 (0-180)
     * @returns {Promise<boolean>} - 성공 여부
     */
    async setAngle2(angle) {
        if (angle < 0) angle = 0;
        if (angle > 180) angle = 180;

        try {
            // SERVO2 명령어로 두 번째 서보 제어
            const result = await this.sendCommand(`SERVO2:${angle}`);
            if (result) {
                this.currentAngle2 = angle;
            }
            return result;
        } catch (error) {
            console.error(`[ServoMotor] 두 번째 서보 각도 설정 오류: ${error.message}`);
            throw error;
        }
    }
    
    /**
     * 특정 서보의 각도 설정
     * @param {number} index - 서보 인덱스 (1 또는 2)
     * @param {number} angle - 각도 (0-180)
     * @returns {Promise<boolean>} - 성공 여부
     */
    async setAngleByIndex(index, angle) {
        if (index === 2) {
            return await this.setAngle2(angle);
        }
        return await this.setAngle(angle);
    }

    /**
     * 서보모터 핀 설정 (첫 번째 서보)
     * @param {number} pin - 모터 핀
     * @returns {Promise<boolean>} - 성공 여부
     */
    async setPin(pin) {
        return await this.sendCommand(`SERVO:PIN:${pin}`);
    }
    
    /**
     * 두 번째 서보모터 핀 설정
     * @param {number} pin - 모터 핀
     * @returns {Promise<boolean>} - 성공 여부
     */
    async setPin2(pin) {
        return await this.sendCommand(`SERVO:PIN2:${pin}`);
    }
    
    /**
     * 특정 서보의 핀 설정
     * @param {number} index - 서보 인덱스 (1 또는 2)
     * @param {number} pin - 모터 핀
     * @returns {Promise<boolean>} - 성공 여부
     */
    async setPinByIndex(index, pin) {
        if (index === 2) {
            return await this.setPin2(pin);
        }
        return await this.setPin(pin);
    }

    /**
     * 서보모터 데이터 처리
     * @param {*} data - 수신 데이터
     */
    _processData(data) {
        if (!data) return;

        const dataStr = data.toString();


    }
}

/**
 * 카메라 클래스
 * SensorBase 상속
 */
class Camera extends SensorBase {
    /**
     * 카메라 클래스 생성자
     */
    constructor() {
        super('Camera', CAM_CHARACTERISTIC);

        // 카메라 상태 및 이미지 관련 변수
        this.isStreaming = false;
        this.currentFrameSize = 0;
        this.frameChunks = [];
        this.expectedChunks = 0;
        this.receivingFrame = false;
        this.latestImage = null;
        this.latestImageDate = null;
        this.streamInterval = 200; // 기본 스트리밍 간격 (ms)

        // 이미지 이벤트 콜백
        this.onImageComplete = null;
        this.onStreamingStateChange = null;

        // 로깅
        EZ_LOG.info("[Camera] 카메라 모듈 초기화됨");
    }

    /**
     * 한 장의 사진 촬영
     * @returns {Promise<boolean>} - 명령 전송 성공 여부
     */
    async takeSnapshot() {
        EZ_LOG.info("[Camera] 사진 촬영 요청");
        return await this.sendCommand("CAM:SNAP");
    }

    /**
     * 카메라 스트리밍 시작
     * @returns {Promise<boolean>} - 명령 전송 성공 여부
     */
    async startStreaming() {
        EZ_LOG.info("[Camera] 스트리밍 시작 요청");

        try {
            // 먼저 스트리밍 간격 설정
            await this.setStreamInterval(this.streamInterval);

            // 스트리밍 시작 명령 전송
            const result = await this.sendCommand("CAM:STREAM:ON");
            if (result) {
                this.isStreaming = true;

                // 스트리밍 상태 변경 콜백 호출
                if (typeof this.onStreamingStateChange === 'function') {
                    this.onStreamingStateChange(true);
                }
            }

            return result;
        } catch (error) {
            EZ_LOG.error(`[Camera] 스트리밍 시작 실패: ${error.message}`);
            throw error;
        }
    }

    /**
     * 카메라 스트리밍 중지
     * @returns {Promise<boolean>} - 명령 전송 성공 여부
     */
    async stopStreaming() {
        EZ_LOG.info("[Camera] 스트리밍 중지 요청");

        try {
            const result = await this.sendCommand("CAM:STREAM:OFF");
            if (result) {
                this.isStreaming = false;

                // 스트리밍 상태 변경 콜백 호출
                if (typeof this.onStreamingStateChange === 'function') {
                    this.onStreamingStateChange(false);
                }
            }

            return result;
        } catch (error) {
            EZ_LOG.error(`[Camera] 스트리밍 중지 실패: ${error.message}`);
            throw error;
        }
    }

    /**
     * 스트리밍 간격 설정
     * @param {number} intervalMs - 간격 (밀리초, 100-1000 사이)
     * @returns {Promise<boolean>} - 명령 전송 성공 여부
     */
    async setStreamInterval(intervalMs) {
        // 범위 제한
        if (intervalMs < 100) intervalMs = 100;
        if (intervalMs > 1000) intervalMs = 1000;

        this.streamInterval = intervalMs;
        EZ_LOG.info(`[Camera] 스트리밍 간격 설정: ${intervalMs}ms`);

        return await this.sendCommand(`CAM:INTERVAL ${intervalMs}`);
    }

    //  Blob 파일 가져오기
    async getNewImageBlob() {
        //  가장 마지막으로 사진 찍은 데이터 값 가져오기
        let beforImgDate = this.latestImageDate;
        //  사진 캡쳐 오청
        this.takeSnapshot();

        return new Promise((resolve, reject) => {
            try {
                //  새로운 사진 없으면 계속 요청
                let timmer = setInterval(() => {
                    //  이전 캡쳐 시간과 현재 캡쳐 시간이 같이 않는다면
                    if (beforImgDate != this.latestImageDate) {
                        //  타이머 종료
                        clearInterval(timmer);
                        //  blob파일 리턴
                        resolve(this.latestImage);
                    }
                }, 300)
            } catch (error) {
                reject(error)
            }
        })
    }

    /**
     * 이미지 완료 이벤트 콜백 설정
     * @param {Function} callback - 이미지가 완성될 때 호출될 콜백 함수, 인자로 Blob 객체를 받음
     */
    setOnImageComplete(callback) {
        if (typeof callback === 'function') {
            this.onImageComplete = callback;
        }
    }

    /**
     * 스트리밍 상태 변경 이벤트 콜백 설정
     * @param {Function} callback - 스트리밍 상태가 변경될 때 호출될 콜백 함수, 인자로 boolean을 받음
     */
    setOnStreamingStateChange(callback) {
        if (typeof callback === 'function') {
            this.onStreamingStateChange = callback;
        }
    }

    /**
     * 가장 최근에 완성된 이미지 반환
     * @returns {Blob|null} - 이미지 Blob 객체 또는 null
     */
    getLatestImage() {
        return this.latestImage;
    }

    /**
     * 스트리밍 중인지 여부 반환
     * @returns {boolean} - 스트리밍 중인지 여부
     */
    isStreamingActive() {
        return this.isStreaming;
    }

    /**
     * 카메라 데이터 처리
     * @param {*} data - 수신 데이터
     */
    _processData(data) {
        if (!data) return;

        // 데이터가 ArrayBuffer, DataView, TypedArray인 경우 처리
        if (data.data instanceof ArrayBuffer ||
            data.data instanceof DataView ||
            (data.data && data.data.buffer instanceof ArrayBuffer)) {
            this._processRawData(data.data);
            return;
        }

        // 문자열로 변환
        let dataStr;
        try {
            if (data.data) {
                // 중첩 데이터 구조 처리
                if (typeof data.data.toString === 'function') {
                    dataStr = data.data.toString();
                } else {
                    dataStr = String(data.data);
                }
            } else if (typeof data.toString === 'function') {
                dataStr = data.toString();
            } else {
                dataStr = String(data);
            }
        } catch (e) {
            EZ_LOG.error(`[Camera] 데이터 변환 오류: ${e.message}`);
            dataStr = String(data || "");
        }

        this._processTextCommand(dataStr);
    }

    /**
     * 원시 데이터 처리 (이진 데이터)
     * @param {ArrayBuffer|DataView|TypedArray} rawData - 원시 이진 데이터
     */
    _processRawData(rawData) {
        // 데이터를 텍스트로 변환 시도 (헤더 확인용)
        try {
            const decoder = new TextDecoder('utf-8');
            let dataView;

            if (rawData instanceof ArrayBuffer) {
                dataView = new DataView(rawData);
            } else if (rawData instanceof DataView) {
                dataView = rawData;
            } else if (rawData.buffer instanceof ArrayBuffer) {
                dataView = new DataView(rawData.buffer, rawData.byteOffset, rawData.byteLength);
            } else {
                // 처리할 수 없는 데이터 형식
                EZ_LOG.error(`[Camera] 처리할 수 없는 데이터 형식: ${typeof rawData}`);
                return;
            }

            // 처음 20바이트만 문자열로 변환해서 헤더 확인
            const headerBytes = new Uint8Array(dataView.buffer, dataView.byteOffset, Math.min(20, dataView.byteLength));
            const headerStr = decoder.decode(headerBytes);

            if (headerStr.startsWith("BIN")) {
                // 바이너리 청크 데이터 처리
                this._processBinaryChunk(dataView, headerStr);
            } else {
                // 일반 텍스트 명령어
                const fullText = decoder.decode(dataView);
                this._processTextCommand(fullText);
            }
        } catch (e) {
            EZ_LOG.error(`[Camera] 이진 데이터 처리 오류: ${e.message}`);
        }
    }

    /**
     * 텍스트 명령어 처리
     * @param {string} text - 텍스트 명령어
     */
    _processTextCommand(text) {
        if (!text) return;

        // 일부 로깅 (너무 길면 잘라서 표시)
        const logText = text.length > 30 ? text.substring(0, 30) + "..." : text;
        EZ_LOG.debug(`[Camera] 수신 텍스트: ${logText}`);

        if (text.startsWith("CAM:START")) {
            // 새 프레임 시작
            EZ_LOG.debug("[Camera] 새 프레임 수신 시작");
            this.receivingFrame = true;
            this.frameChunks = [];
            this.currentFrameSize = 0;
            this.expectedChunks = 0;
            /////////////////////////////////////////////////////////////////////////////////////////
            // 보드 펌웨어와 동일한 청크 크기(현재 펌웨어: 160 bytes)
            this.chunkSize = 160;
        }
        else if (text.startsWith("SIZE:") && this.receivingFrame) {
            // 프레임 크기 정보
            try {
                this.currentFrameSize = parseInt(text.substring(5));
                EZ_LOG.info(`[Camera] 프레임 크기: ${this.currentFrameSize} 바이트`);

                // 예상 청크 수 계산 (160바이트 청크 기준)
                this.expectedChunks = Math.ceil(this.currentFrameSize / this.chunkSize);
            } catch (e) {
                EZ_LOG.error(`[Camera] 프레임 크기 파싱 오류: ${e.message}`);
                this.receivingFrame = false;
            }
        }
        else if (text === "CAM:END" && this.receivingFrame) {
            // 프레임 수신 완료
            EZ_LOG.info(`[Camera] 프레임 수신 완료: ${this.frameChunks.length} 청크`);
            this._assembleImageFromChunks();
        }
        else if (text === "CAM:ERROR") {
            EZ_LOG.error("[Camera] 카메라 오류 발생");
            this.receivingFrame = false;
            this.frameChunks = [];
        }
    }

    /**
     * 바이너리 청크 처리
     * @param {DataView} dataView - 데이터 뷰
     * @param {string} headerStr - 헤더 문자열
     */
    _processBinaryChunk(dataView, headerStr) {
        if (!this.receivingFrame) {
            EZ_LOG.debug("[Camera] 프레임 수신 중이 아닌데 청크 데이터가 도착했습니다.");
            return;
        }

        try {
            // 헤더와 데이터 분리 지점 찾기
            const colonIndex = headerStr.indexOf(':');
            if (colonIndex <= 0) {
                EZ_LOG.error("[Camera] 유효하지 않은 바이너리 헤더 형식");
                return;
            }

            // 시퀀스 번호 추출 (BIN 뒤의 숫자)
            const seqNumStr = headerStr.substring(3, colonIndex);
            const seqNum = parseInt(seqNumStr);
            if (isNaN(seqNum)) {
                EZ_LOG.error(`[Camera] 유효하지 않은 시퀀스 번호: ${seqNumStr}`);
                return;
            }

            // 헤더 부분 계산 (BINxx: 형식)
            const headerLength = colonIndex + 1;

            // 실제 이미지 데이터만 추출 (헤더 제외)
            const imageData = new Uint8Array(
                dataView.buffer,
                dataView.byteOffset + headerLength,
                dataView.byteLength - headerLength
            );

            // 청크 저장
            this.frameChunks.push({
                seqNum: seqNum,
                data: imageData
            });

            // 고빈도 로그는 debug에서만 (info에서는 프레임 단위 요약만)
            EZ_LOG.debug(`[Camera] 청크 ${seqNum} 수신 (${this.frameChunks.length}/${this.expectedChunks})`);
        } catch (e) {
            EZ_LOG.error(`[Camera] 바이너리 청크 처리 오류: ${e.message}`);
        }
    }

    /**
     * 청크에서 이미지 조립
     */
    _assembleImageFromChunks() {
        this.receivingFrame = false;

        if (this.frameChunks.length === 0) {
            EZ_LOG.error("[Camera] 수신된 이미지 청크가 없습니다.");
            return;
        }

        try {
            // 청크를 시퀀스 번호로 정렬
            this.frameChunks.sort((a, b) => a.seqNum - b.seqNum);

            // 청크들을 하나의 blob으로 조합
            const chunks = this.frameChunks.map(chunk => chunk.data);
            const blob = new Blob(chunks, { type: 'image/jpeg' });

            // 최신 이미지 업데이트
            this.latestImage = blob;
            this.latestImageDate = new Date().valueOf();

            // 이미지 완료 콜백 호출
            if (typeof this.onImageComplete === 'function') {
                this.onImageComplete(blob);
            }

            EZ_LOG.info(`[Camera] 이미지 조립 완료: ${blob.size} 바이트`);
        } catch (e) {
            EZ_LOG.error(`[Camera] 이미지 조립 오류: ${e.message}`);
        } finally {
            // 메모리 해제
            this.frameChunks = [];
        }
    }
}



////////////////////////////////////////////////////////////////////////////////////////////////////////////////
// 활성 타이머 ID를 저장할 전역 변수
let activeBlinkTimerId = null;

/**
 * LED를 지정된 간격으로 깜빡이게 하는 함수
 * 같은 LED에 대해 여러 번 호출해도 하나의 타이머만 실행됨
 * @param {Object} led - LED 객체 (turnOn, turnOff 메소드 필요)
 * @param {number} interval - 깜빡임 간격 (밀리초)
 * @returns {number} 타이머 ID (나중에 clearInterval로 정지할 때 사용)
 */
function blinkLED(led, interval = 500) {
    // 이미 실행 중인 타이머가 있으면 중지
    if (activeBlinkTimerId !== null) {
        stopBlinking(led);
    }

    // LED 상태
    let isOn = false;

    // 타이머 시작
    activeBlinkTimerId = setInterval(() => {
        // LED 상태 반전
        if (isOn) {
            led.turnOff();
        } else {
            led.turnOn();
        }

        // 상태 업데이트
        isOn = !isOn;
    }, interval);

    // 타이머 ID 반환 (정지할 때 사용)
    return activeBlinkTimerId;
}

/**
 * LED 깜빡임을 정지하는 함수
 * @param {Object} led - LED 객체 (상태 초기화용)
 * @param {boolean} turnOffWhenStop - 정지시 LED를 끌지 여부 (기본값: true)
 */
function stopBlinking(led, turnOffWhenStop = true) {
    // 활성 타이머가 있는 경우에만 정지
    if (activeBlinkTimerId !== null) {
        // 타이머 정지
        clearInterval(activeBlinkTimerId);

        // LED 상태 초기화 (선택적)
        if (turnOffWhenStop) {
            led.turnOff();
        }

        // 타이머 ID 초기화
        activeBlinkTimerId = null;

    }
    led.turnOff();
}










/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////







/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////



/**
 * 먼지 센서 클래스
 * SensorBase 상속
 */
class DustSensor extends SensorBase {
    /**
     * 먼지 센서 클래스 생성자
     */
    constructor() {
        super('Dust', DUST_CHARACTERISTIC);
        this.density = null;    // 먼지 농도 (μg/m³)
        this.voltage = null;    // 측정 전압 (V)
        this.rawValue = null;   // 원시 ADC 값
        this.voc = null;        // 보정 기준값 (V)
        this._isCalibrated = false; // 보정 완료 여부
        this.calibrationCallbacks = []; // 보정 완료 콜백 배열 추가
    }

    /**
     * 먼지 농도 값 반환
     * @returns {number|null} - 먼지 농도(μg/m³) 또는 null
     */
    getDensity() {
        return this.density;
    }

    /**
     * 측정 전압 반환
     * @returns {number|null} - 전압(V) 또는 null
     */
    getVoltage() {
        return this.voltage;
    }

    /**
     * 원시 ADC 값 반환
     * @returns {number|null} - 원시 ADC 값 또는 null
     */
    getRawValue() {
        return this.rawValue;
    }

    /**
     * 보정 기준값 (VOC) 반환
     * @returns {number|null} - 보정 기준값(V) 또는 null
     */
    getVoc() {
        return this.voc;
    }

    /**
     * 보정 여부 반환
     * @returns {boolean} - 보정 완료 여부
     */
    isCalibrated() {
        return this._isCalibrated;
    }

    /**
     * 먼지 센서 상태 요청
     * @returns {Promise<boolean>} - 성공 여부
     */
    async getStatus() {
        console.log("먼지 센서 상태 요청 전송");
        return await this.sendCommand("DUST:STATUS");
    }

    /**
     * 먼지 센서 보정 실행
     * @returns {Promise<boolean>} - 성공 여부
     */
    async calibrate() {
        console.log("먼지 센서 보정 요청 전송");
        return await this.sendCommand("DUST:CALIBRATE");
    }

    /**
     * 먼지 센서 핀 설정
     * @param {number} ledPin - LED 핀 번호
     * @param {number} adcPin - ADC 핀 번호
     * @returns {Promise<boolean>} - 성공 여부
     */
    async setPin(ledPin, adcPin) {
        return await this.sendCommand(`DUST:PIN:${ledPin},${adcPin}`);
    }

    /**
     * 보정 완료 이벤트 핸들러 등록
     * @param {Function} callback - 보정 완료 시 호출될 콜백 함수, VOC 값을 매개변수로 전달받음
     */
    onCalibrationComplete(callback) {
        if (typeof callback === 'function') {
            this.calibrationCallbacks.push(callback);
            console.log("[DustSensor] 보정 완료 콜백 등록됨");
            return true;
        }
        return false;
    }

    /**
     * 먼지 센서 데이터 처리
     * @param {*} data - 수신 데이터
     */
    _processData(data) {
        if (!data) return;

        console.log("[DustSensor] 데이터 수신 확인:", data);

        // 데이터 형식 확인 - data.data 구조 처리 추가
        let actualData = data;
        if (data && typeof data === 'object' && data.data !== undefined) {
            console.log("[DustSensor] data.data 구조 감지, 내부 데이터 사용");
            actualData = data.data;  // 중첩된 구조 처리
        }

        // 데이터 변환 시도
        let dataStr;
        try {
            // ArrayBuffer 또는 DataView인 경우 텍스트로 변환
            if (actualData instanceof ArrayBuffer) {
                const decoder = new TextDecoder('utf-8');
                dataStr = decoder.decode(new DataView(actualData));
                console.log("[DustSensor] ArrayBuffer에서 변환된 문자열:", dataStr);
            } else if (actualData instanceof DataView) {
                const decoder = new TextDecoder('utf-8');
                dataStr = decoder.decode(actualData);
                console.log("[DustSensor] DataView에서 변환된 문자열:", dataStr);
            } else if (actualData && actualData.buffer instanceof ArrayBuffer) {
                // TypedArray 처리 (Uint8Array 등)
                const decoder = new TextDecoder('utf-8');
                dataStr = decoder.decode(actualData);
                console.log("[DustSensor] TypedArray에서 변환된 문자열:", dataStr);
            } else {
                // 문자열이거나 다른 타입으로 안전하게 변환
                dataStr = String(actualData);
                console.log("[DustSensor] 기본 변환 문자열:", dataStr);
            }
        } catch (e) {
            console.error("[DustSensor] 데이터 변환 오류:", e);
            dataStr = String(actualData || "");
            console.log("[DustSensor] 오류 후 강제 변환 문자열:", dataStr);
        }

        // 먼지 센서 값 파싱
        try {
            // DUST:먼지농도,전압,원시값 형식 처리
            if (dataStr.startsWith("DUST:") && dataStr.includes(",")) {
                const valueStr = dataStr.substring(5); // "DUST:" 제거
                const parts = valueStr.split(",");

                if (parts.length >= 3) {
                    this.density = parseFloat(parts[0]);
                    this.voltage = parseFloat(parts[1]);
                    this.rawValue = parseFloat(parts[2]);

                    console.log(`[DustSensor] 파싱된 값: 먼지농도=${this.density}μg/m³, 전압=${this.voltage}V, 원시값=${this.rawValue}`);
                }
            }
            // 보정 관련 응답 처리 - 개선된 부분
            else if (dataStr.includes("DUST:CALIBRATE:DONE")) {
                console.log("#####################[DustSensor] 보정 완료 응답 수신");
                const vocMatch = dataStr.match(/DONE:([0-9.]+)/);
                if (vocMatch && vocMatch.length > 1) {
                    const vocValue = parseFloat(vocMatch[1]);
                    this.voc = vocValue;
                    this._isCalibrated = true;
                    console.log(`[DustSensor] 보정 완료: VOC=${this.voc}V`);

                    // 보정 완료 이벤트 발생
                    this._triggerCalibrationCallbacks(vocValue);

                    // 보정 완료 알림 표시 (선택적)
                    if (typeof showNotification === 'function') {
                        showNotification('먼지 센서 보정 완료', `기준값(VOC): ${vocValue.toFixed(3)}V로 설정되었습니다.`);
                    }
                }
            }
            // 다른 형식 처리 - DUST:DENSITY=밀도,VOC=VOC값
            else if (dataStr.includes("DUST:DENSITY=") && dataStr.includes("VOC=")) {
                const densityMatch = dataStr.match(/DENSITY=([0-9.]+)/);
                const vocMatch = dataStr.match(/VOC=([0-9.]+)/);

                if (densityMatch && densityMatch.length > 1) {
                    this.density = parseFloat(densityMatch[1]);
                    console.log(`[DustSensor] 먼지 농도: ${this.density}μg/m³`);
                }

                if (vocMatch && vocMatch.length > 1) {
                    this.voc = parseFloat(vocMatch[1]);
                    console.log(`[DustSensor] VOC 값: ${this.voc}V`);
                }
            }
        } catch (error) {
            console.error(`[DustSensor] 데이터 파싱 오류: ${error.message}`);
        }
    }

    /**
     * 등록된 보정 완료 콜백 함수들을 실행
     * @param {number} vocValue - 보정된 VOC 값
     * @private
     */
    _triggerCalibrationCallbacks(vocValue) {
        if (this.calibrationCallbacks.length > 0) {
            console.log(`[DustSensor] ${this.calibrationCallbacks.length}개의 보정 완료 콜백 실행`);
            this.calibrationCallbacks.forEach(callback => {
                try {
                    callback({
                        voc: vocValue,
                        success: true,
                        timestamp: new Date()
                    });
                } catch (error) {
                    console.error('[DustSensor] 보정 콜백 실행 오류:', error);
                }
            });
        }
    }
}

/**
 * 먼지 센서에서 측정값을 가져오는 함수 (재시도 로직 포함)
 * @param {Object} sensor - 먼지 센서 객체 (getStatus, getDensity 메소드 필요)
 * @param {number} maxRetries - 최대 재시도 횟수 (기본값: 3)
 * @param {number} retryDelay - 재시도 간격 (밀리초, 기본값: 50)
 * @returns {Promise<{density: number|null, voltage: number|null, rawValue: number|null}|null>} 먼지 측정 정보 또는 null
 */
function getDustSensorValue(sensor, maxRetries = 3, retryDelay = 50) {
    let retries = 0;

    function tryGetValue() {
        // 센서가 null이거나 undefined인 경우 처리
        if (!sensor) {
            console.log("먼지 센서 객체가 없습니다");
            return Promise.resolve(null);
        }

        // 보정 완료 여부 확인 추가
        const isCalibrationCheckerAvailable = typeof sensor.isCalibrated === 'function';
        if (isCalibrationCheckerAvailable) {
            const calibrated = sensor.isCalibrated();
            if (!calibrated) {
                console.log("먼지 센서가 보정되지 않았습니다. 먼저 보정을 수행하세요.");
                return Promise.resolve({
                    density: null,
                    voltage: null,
                    rawValue: null,
                    calibrationNeeded: true
                });
            }
        }

        return sensor.getStatus().then(() => {
            // 메소드 존재 여부 확인
            const hasDensity = typeof sensor.getDensity === 'function';
            const hasVoltage = typeof sensor.getVoltage === 'function';
            const hasRawValue = typeof sensor.getRawValue === 'function';

            if (!hasDensity && !hasVoltage && !hasRawValue) {
                console.log("먼지 센서에 필요한 메소드가 없습니다");
                return null;
            }

            // 측정값 가져오기
            const density = hasDensity ? sensor.getDensity() : null;
            const voltage = hasVoltage ? sensor.getVoltage() : null;
            const rawValue = hasRawValue ? sensor.getRawValue() : null;

            // 모든 값이 null이고 재시도 횟수가 남아있으면 재시도
            if ((density === null && voltage === null && rawValue === null) && retries < maxRetries) {
                retries++;
                console.log(`먼지 센서 값이 null, 재시도 ${retries}/${maxRetries}`);

                // 재시도를 위한 지연 및 재귀 호출
                return new Promise(resolve => {
                    setTimeout(() => resolve(tryGetValue()), retryDelay);
                });
            }

            // 유효한 값이나 최대 재시도 후 최종 값 반환
            return { density, voltage, rawValue };
        });
    }

    return tryGetValue();
}

/**
 * 먼지 센서에서 유효한 측정값을 가져오는 헬퍼 함수
 * @param {Object} sensor - 먼지 센서 객체
 * @returns {Promise<{density: number, voltage: number, rawValue: number}>} - 유효한 먼지 측정값
 * @throws {Error} - 유효한 값이 없을 경우 오류 발생
 */
async function getValidDustValue(sensor) {
    const result = await getDustSensorValue(sensor);
    if (!result) {
        throw new Error("먼지 센서 값을 가져올 수 없습니다");
    }

    // 적어도 하나의 유효한 값이 있는지 확인
    const hasValidDensity = result.density !== null && result.density !== undefined;
    const hasValidVoltage = result.voltage !== null && result.voltage !== undefined;
    const hasValidRawValue = result.rawValue !== null && result.rawValue !== undefined;

    if (!hasValidDensity && !hasValidVoltage && !hasValidRawValue) {
        throw new Error("유효한 먼지 센서 값이 없습니다");
    }

    // 유효한 값만 포함한 객체 반환 (없는 값은 null로 유지)
    return {
        density: hasValidDensity ? result.density : null,
        voltage: hasValidVoltage ? result.voltage : null,
        rawValue: hasValidRawValue ? result.rawValue : null
    };
}


/**
 * NeoPixel LED 클래스
 * SensorBase 상속
 */
class NeoPixel extends SensorBase {
    /**
     * NeoPixel 클래스 생성자
     */
    constructor() {
        super('NeoPixel', NEOPIXEL_CHARACTERISTIC);
        this.numPixels = 0;      // LED 픽셀 개수
        this.pixelColors = [];   // 각 픽셀의 색상 저장
        this.isRainbowActive = false; // 무지개 효과 활성화 상태
        this.brightness = 1.0;   // 밝기 (0.0-1.0, 기본값 100%)
    }

    /**
     * 픽셀 개수 반환
     * @returns {number} - 픽셀 개수
     */
    getNumPixels() {
        return this.numPixels;
    }

    /**
     * 무지개 효과 활성화 상태 반환
     * @returns {boolean} - 무지개 효과 활성화 여부
     */
    isRainbowMode() {
        return this.isRainbowActive;
    }

    /**
     * 현재 밝기 반환
     * @returns {number} - 밝기 (0.0-1.0)
     */
    getBrightness() {
        return this.brightness;
    }

    /**
     * 특정 픽셀의 현재 색상 반환
     * @param {number} index - 픽셀 인덱스 (0부터 시작)
     * @returns {Object|null} - {r, g, b} 형태의 색상 객체 또는 null
     */
    getPixelColor(index) {
        if (index >= 0 && index < this.pixelColors.length) {
            return this.pixelColors[index];
        }
        return null;
    }

    /**
     * 밝기 설정
     * @param {number} brightness - 밝기값 (0-255)
     * @returns {Promise<boolean>} - 성공 여부
     */
    async setBrightness(brightness) {
        // 0-255 사이의 값으로 제한
        brightness = Math.min(255, Math.max(0, brightness));
        
        try {
            // 밝기 명령 전송
            const result = await this.sendCommand(`NEO:BRIGHTNESS:${brightness}`);
            
            // 성공시 내부 상태 업데이트
            if (result) {
                // 0-255에서 0.0-1.0 범위로 변환
                this.brightness = brightness / 255.0;
                console.log(`[NeoPixel] 밝기 설정: ${brightness}`);
            }
            
            return result;
        } catch (error) {
            console.error(`[NeoPixel] 밝기 설정 오류: ${error.message}`);
            throw error;
        }
    }

    /**
     * NeoPixel 핀 설정
     * @param {number} pin - 데이터 핀 번호
     * @param {number} numPixels - LED 픽셀 개수 (기본값: 4)
     * @returns {Promise<boolean>} - 성공 여부
     */
    async setPin(pin, numPixels = 4) {
        this.numPixels = numPixels;

        // 픽셀 색상 배열 초기화
        this.pixelColors = Array(numPixels).fill().map(() => ({ r: 0, g: 0, b: 0 }));

        return await this.sendCommand(`NEO:PIN:${pin},${numPixels}`);
    }

    /**
     * 특정 픽셀의 색상 설정
     * @param {number} index - 픽셀 인덱스 (0부터 시작)
     * @param {number} r - 빨간색 값 (0-255)
     * @param {number} g - 초록색 값 (0-255)
     * @param {number} b - 파란색 값 (0-255)
     * @returns {Promise<boolean>} - 성공 여부
     */
    async setPixelColor(index, colorCode) {
        //  색상 코드 가져오기
        let color = this.setRgbCode(colorCode)

        // 색상 값 범위 확인 및 조정
        let r = Math.min(255, Math.max(0, color.r));
        let g = Math.min(255, Math.max(0, color.g));
        let b = Math.min(255, Math.max(0, color.b));

        console.log(`111111111111111111[NeoPixel] 픽셀 색상 설정: ${index}, ${r}, ${g}, ${b}`);

        try {
            //const result = await this.sendCommand(`NEO:PIXEL:${index},${r},${g},${b}`);
            const result = await this.sendCommand(`NEO:PX:${index},${r},${g},${b}`);


            // 성공시 내부 상태 업데이트
            if (result && index >= 0 && index < this.numPixels) {
                this.pixelColors[index] = { r, g, b };
                this.isRainbowActive = false; // 픽셀 색상을 직접 설정하면 무지개 모드 비활성화
            }

            return result;
        } catch (error) {
            console.error(`[NeoPixel] 픽셀 색상 설정 오류: ${error.message}`);
            throw error;
        }
    }

    /**
   * 특정 픽셀의 색상 설정
   * @param {number} index - 픽셀 인덱스 (0부터 시작)
   * @param {number} r - 빨간색 값 (0-255)
   * @param {number} g - 초록색 값 (0-255)
   * @param {number} b - 파란색 값 (0-255)
   * @returns {Promise<boolean>} - 성공 여부
   */
  async setPixelColor1(index, r, g, b) {
    // 색상 값 범위 확인 및 조정
    r = Math.min(255, Math.max(0, r));
    g = Math.min(255, Math.max(0, g));
    b = Math.min(255, Math.max(0, b));

    console.log(`111111111111111111[NeoPixel] 픽셀 색상 설정: ${index}, ${r}, ${g}, ${b}`);
    
    try {
      //const result = await this.sendCommand(`NEO:PIXEL:${index},${r},${g},${b}`);
      const result = await this.sendCommand(`NEO:PX:${index},${r},${g},${b}`);
      
      
      // 성공시 내부 상태 업데이트
      if (result && index >= 0 && index < this.numPixels) {
        this.pixelColors[index] = { r, g, b };
        this.isRainbowActive = false; // 픽셀 색상을 직접 설정하면 무지개 모드 비활성화
      }
      
      return result;
    } catch (error) {
      console.error(`[NeoPixel] 픽셀 색상 설정 오류: ${error.message}`);
      throw error;
    }
  }

    /**
     * 모든 픽셀 색상 한번에 설정
     * @param {number} r - 빨간색 값 (0-255)
     * @param {number} g - 초록색 값 (0-255)
     * @param {number} b - 파란색 값 (0-255)
     * @returns {Promise<boolean>} - 성공 여부
     */
    async setAllPixels(colorCode) {
        //  색상 코드 가져오기
        let color = this.setRgbCode(colorCode)

        // 색상 값 범위 확인 및 조정
        let r = Math.min(255, Math.max(0, color.r));
        let g = Math.min(255, Math.max(0, color.g));
        let b = Math.min(255, Math.max(0, color.b));

        try {
            const result = await this.sendCommand(`NEO:ALL:${r},${g},${b}`);

            // 성공시 내부 상태 업데이트
            if (result) {
                this.pixelColors = Array(this.numPixels).fill().map(() => ({ r, g, b }));
                this.isRainbowActive = false; // 모든 픽셀 색상을 설정하면 무지개 모드 비활성화
            }

            return result;
        } catch (error) {
            console.error(`[NeoPixel] 모든 픽셀 색상 설정 오류: ${error.message}`);
            throw error;
        }
    }

    //  색상코드에서 RGB 값 가져오기
    setRgbCode(color) {
        let red = parseInt(color.slice(1, 3), 16);
        let green = parseInt(color.slice(3, 5), 16);
        let blue = parseInt(color.slice(5, 7), 16);

        return { r: red, g: green, b: blue };
    }

    /**
     * 모든 픽셀 끄기 (검은색으로 설정)
     * @returns {Promise<boolean>} - 성공 여부
     */
    async turnOff() {
        try {
            const result = await this.sendCommand("NEO:OFF");

            // 성공시 내부 상태 업데이트
            if (result) {
                this.pixelColors = Array(this.numPixels).fill().map(() => ({ r: 0, g: 0, b: 0 }));
                this.isRainbowActive = false;
            }

            return result;
        } catch (error) {
            console.error(`[NeoPixel] 픽셀 끄기 오류: ${error.message}`);
            throw error;
        }
    }

    /**
     * 무지개 효과 설정
     * @param {number} speed - 효과 속도 (1-10)
     * @returns {Promise<boolean>} - 성공 여부
     */
    async setRainbow(speed = 5) {
        // 속도 범위 제한
        speed = Math.min(10, Math.max(1, speed));

        try {
            const result = await this.sendCommand(`NEO:RAINBOW:${speed}`);

            // 성공시 무지개 모드 활성화
            if (result) {
                this.isRainbowActive = true;
            }

            return result;
        } catch (error) {
            console.error(`[NeoPixel] 무지개 효과 설정 오류: ${error.message}`);
            throw error;
        }
    }

    /**
     * NeoPixel 데이터 처리
     * @param {*} data - 수신 데이터
     */
    _processData(data) {
        if (!data) return;

        // 데이터가 객체인지 확인하고 데이터 추출
        let dataStr;
        try {
            // 중첩된 data 객체 처리
            if (data.data) {
                const decoder = new TextDecoder('utf-8');

                if (data.data instanceof ArrayBuffer) {
                    dataStr = decoder.decode(new DataView(data.data));
                } else if (data.data instanceof DataView) {
                    dataStr = decoder.decode(data.data);
                } else if (data.data.buffer instanceof ArrayBuffer) {
                    dataStr = decoder.decode(data.data);
                } else {
                    dataStr = String(data.data);
                }
            } else if (typeof data.toString === 'function') {
                dataStr = data.toString();
            } else {
                dataStr = String(data);
            }
        } catch (e) {
            console.error(`[NeoPixel] 데이터 변환 오류: ${e.message}`);
            dataStr = String(data || "");
        }

        // NeoPixel 응답 파싱
        if (dataStr.startsWith("NEO:")) {
            // 픽셀 색상 설정 응답
            if (dataStr.includes("PIXEL:") && dataStr.includes(":OK")) {
                // 성공적인 색상 설정 - 이미 명령 처리에서 상태 업데이트함
                console.log("[NeoPixel] 픽셀 색상 설정 성공");
            }
            // 모든 픽셀 색상 설정 응답
            else if (dataStr.includes("SETALL:") && dataStr.includes(":OK")) {
                console.log("[NeoPixel] 모든 픽셀 색상 설정 성공");
            }
            // 무지개 효과 응답
            else if (dataStr.includes("RAINBOW:") && dataStr.includes(":OK")) {
                this.isRainbowActive = true;
                console.log("[NeoPixel] 무지개 효과 설정 성공");
            }
            // 끄기 응답
            else if (dataStr.includes("OFF") && dataStr.includes(":OK")) {
                console.log("[NeoPixel] 모든 픽셀 끄기 성공");
            }
            // 핀 설정 응답
            else if (dataStr.includes("PIN:") && dataStr.includes(":OK")) {
                // 핀 설정 성공 (numPixels는 이미 명령 처리에서 설정함)
                console.log("[NeoPixel] 핀 설정 성공");
            }
        }
    }
}



/**
 * 버저 클래스
 * SensorBase 상속
 */
class Buzzer extends SensorBase {
    /**
     * 버저 클래스 생성자
     */
    constructor() {
        super('Buzzer', BUZZER_CHARACTERISTIC);
        this.initialized = false;
        this.isPlaying = false;
        this.currentAction = null; // 'beep', 'melody', null
    }

    /**
     * 버저 초기화
     * @returns {Promise<boolean>} - 성공 여부
     */
    async init() {
        try {
            const result = await this.sendCommand("BUZ:INIT");
            if (result) {
                this.initialized = true;
                console.log("버저 초기화 완료");
            }
            return result;
        } catch (error) {
            console.error(`[Buzzer] 초기화 오류: ${error.message}`);
            throw error;
        }
    }

    /**
     * 비프음 재생
     * @param {number} count - 반복 횟수 (기본값: 1)
     * @param {number} frequency - 주파수(Hz) (기본값: 2000)
     * @param {number} duration - 길이(ms) (기본값: 100)
     * @param {number} interval - 간격(ms) (기본값: 100)
     * @returns {Promise<boolean>} - 성공 여부
     */
    async beep(count = 1, frequency = 2000, duration = 100, interval = 100) {
        // 초기화 확인
        if (!this.initialized) {
            console.error("[Buzzer] 버저가 초기화되지 않았습니다.");
            throw new Error("버저가 초기화되지 않았습니다. 먼저 init()을 호출하세요.");
        }

        try {
            const command = `BUZ:BEEP:${count}:${frequency}:${duration}:${interval}`;
            const result = await this.sendCommand(command);

            if (result) {
                this.isPlaying = true;
                this.currentAction = 'beep';
            }

            return result;
        } catch (error) {
            console.error(`[Buzzer] 비프음 재생 오류: ${error.message}`);
            throw error;
        }
    }

    /**
     * 연속 비프음 재생
     * @param {number} frequency - 주파수(Hz) (기본값: 2000)
     * @returns {Promise<boolean>} - 성공 여부
     */
    async playBeepOn(frequency = 2000) {
        // 초기화 확인
        if (!this.initialized) {
            console.error("[Buzzer] 버저가 초기화되지 않았습니다.");
            throw new Error("버저가 초기화되지 않았습니다. 먼저 init()을 호출하세요.");
        }

        try {
            const command = `BUZ:BEEP:ON:${frequency}`;
            const result = await this.sendCommand(command);

            if (result) {
                this.isPlaying = true;
                this.currentAction = 'continuous';
            }

            return result;
        } catch (error) {
            console.error(`[Buzzer] 연속 비프음 재생 오류: ${error.message}`);
            throw error;
        }
    }

    /**
     * 내장 멜로디 재생
     * @param {string} melodyName - 멜로디 이름
     * @param {number} tempo - 템포 (기본값: 120)
     * @returns {Promise<boolean>} - 성공 여부
     */
    async playMelody(melodyName, tempo = 120) {
        // 초기화 확인
        if (!this.initialized) {
            console.error("[Buzzer] 버저가 초기화되지 않았습니다.");
            throw new Error("버저가 초기화되지 않았습니다. 먼저 init()을 호출하세요.");
        }

        if (!melodyName) {
            throw new Error("멜로디 이름이 필요합니다.");
        }

        try {
            const command = `BUZ:PLAY:${melodyName}:${tempo}`;
            const result = await this.sendCommand(command);

            if (result) {
                this.isPlaying = true;
                this.currentAction = 'melody';
            }

            return result;
        } catch (error) {
            console.error(`[Buzzer] 멜로디 재생 오류: ${error.message}`);
            throw error;
        }
    }

    /**
     * 재생 중지
     * @returns {Promise<boolean>} - 성공 여부
     */
    async stop() {
        // 초기화 확인
        if (!this.initialized) {
            console.error("[Buzzer] 버저가 초기화되지 않았습니다.");
            throw new Error("버저가 초기화되지 않았습니다. 먼저 init()을 호출하세요.");
        }

        try {
            const result = await this.sendCommand("BUZ:STOP");

            if (result) {
                this.isPlaying = false;
                this.currentAction = null;
            }

            return result;
        } catch (error) {
            console.error(`[Buzzer] 중지 오류: ${error.message}`);
            throw error;
        }
    }

    /**
     * 현재 재생 상태 확인
     * @returns {Promise<boolean>} - 재생 중이면 true, 아니면 false
     */
    async getStatus() {
        // 초기화 확인
        if (!this.initialized) {
            console.error("[Buzzer] 버저가 초기화되지 않았습니다.");
            throw new Error("버저가 초기화되지 않았습니다. 먼저 init()을 호출하세요.");
        }

        try {
            await this.sendCommand("BUZ:STATUS");
            // 응답은 _processData 메서드에서 처리됨
            return this.isPlaying;
        } catch (error) {
            console.error(`[Buzzer] 상태 확인 오류: ${error.message}`);
            throw error;
        }
    }

    /**
     * 재생 중인지 여부 반환 (비동기 호출 없이 현재 저장된 상태 반환)
     * @returns {boolean} - 재생 중이면 true, 아니면 false
     */
    isActive() {
        return this.isPlaying;
    }

    /**
     * 버저 데이터 처리
     * @param {*} data - 수신 데이터
     */
    _processData(data) {
        if (!data) return;

        console.log("[Buzzer] 데이터 수신 확인:", data);

        // 데이터 형식 확인 - data.data 구조 처리 추가
        let actualData = data;
        if (data && typeof data === 'object' && data.data !== undefined) {
            console.log("[Buzzer] data.data 구조 감지, 내부 데이터 사용");
            actualData = data.data;  // 중첩된 구조 처리
        }

        // 데이터 변환 시도
        let dataStr;
        try {
            // ArrayBuffer 또는 DataView인 경우 텍스트로 변환
            if (actualData instanceof ArrayBuffer) {
                const decoder = new TextDecoder('utf-8');
                dataStr = decoder.decode(new DataView(actualData));
            } else if (actualData instanceof DataView) {
                const decoder = new TextDecoder('utf-8');
                dataStr = decoder.decode(actualData);
            } else if (actualData && actualData.buffer instanceof ArrayBuffer) {
                // TypedArray 처리 (Uint8Array 등)
                const decoder = new TextDecoder('utf-8');
                dataStr = decoder.decode(actualData);
            } else {
                // 문자열이거나 다른 타입으로 안전하게 변환
                dataStr = String(actualData);
            }
        } catch (e) {
            console.error("[Buzzer] 데이터 변환 오류:", e);
            dataStr = String(actualData || "");
        }

        // 버저 응답 파싱
        if (dataStr === "INITIALIZED" || dataStr === "ALREADY_INITIALIZED") {
            this.initialized = true;
            console.log("[Buzzer] 초기화됨");
        } else if (dataStr === "PLAYING") {
            this.isPlaying = true;
            console.log("[Buzzer] 재생 중");
        } else if (dataStr === "STOPPED") {
            this.isPlaying = false;
            this.currentAction = null;
            console.log("[Buzzer] 정지됨");
        } else if (dataStr === "COMPLETED") {
            this.isPlaying = false;
            this.currentAction = null;
            console.log("[Buzzer] 재생 완료");
        } else if (dataStr.startsWith("ERROR:")) {
            const errorMsg = dataStr.substring(6);
            console.error(`[Buzzer] 오류: ${errorMsg}`);
        }
    }
}


/**
 * DC 모터 제어 클래스
 * 단방향 DC 모터를 위한 클래스로, PWM을 통해 속도 제어 가능
 */
class DCMotor extends SensorBase {
    /**
     * DCMotor 클래스 생성자
     */
    constructor() {
        super('DCMotor', DCMOTOR_CHARACTERISTIC);
        this.currentSpeed = 0;
    }

    /**
     * 현재 모터 속도값 반환
     * @returns {number} 현재 설정된 모터 속도 (0-100%)
     */
    getCurrentSpeed() {
        return this.currentSpeed;
    }

    /**
     * DC 모터 핀 설정
     * @param {number} pin PWM 신호를 출력할 핀 번호
     * @returns {Promise<boolean>} 성공 여부
     */
    async setPin(pin) {
        const response = await this.sendCommand(`MOTOR:PIN:${pin}`);
        /*try {
          
           const success = response && response.includes('MOTOR:PIN:OK');
          if (success) {
            console.log(`[DCMotor] 핀 설정 완료: ${pin}`);
          }
          return success;
        } catch (e) {
          console.error('[DCMotor] 핀 설정 오류:', e);
          return false;
        } */
    }

    /**
     * 모터 속도 설정
     * @param {number} speed 속도 값 (0-100%)
     * @returns {Promise<boolean>} 성공 여부
     */
    async setSpeed(speed) {
        // 속도 값 검증 및 보정
        let validSpeed = Math.max(0, Math.min(100, Math.round(speed)));

        try {
            const response = await this.sendCommand(`MOTOR:SPEED:${validSpeed}`);
            // response가 boolean 타입인 경우 (true) 또는 문자열인 경우(MOTOR:SPEED:OK가 포함된) 처리
            const success = typeof response === 'boolean' ? response : (response && response.includes && response.includes('MOTOR:SPEED:OK'));
            if (success) {
                this.currentSpeed = validSpeed;
                console.log(`[DCMotor] 속도 설정 완료: ${validSpeed}%`);
            }
            return success;
        } catch (e) {
            console.error('[DCMotor] 속도 설정 오류:', e);
            return false;
        }
    }

    /**
     * 모터 정지
     * @returns {Promise<boolean>} 성공 여부
     */
    async stop() {
        try {
            const response = await this.sendCommand('MOTOR:STOP');

            // response가 boolean 타입인 경우 (true) 또는 문자열인 경우(MOTOR:STOP:OK가 포함된) 처리
            const success = typeof response === 'boolean' ? response : (response && response.includes && response.includes('MOTOR:STOP:OK'));

            if (success) {
                this.currentSpeed = 0;
                console.log('[DCMotor] 모터 정지');
            }
            return success;
        } catch (e) {
            console.error('[DCMotor] 모터 정지 오류:', e);
            return false;
        }
    }

    /**
     * 데이터 처리
     * @param {string|Uint8Array} data 수신된 데이터
     * @private
     */
    _processData(data) {
        let dataStr;

        try {
            if (data instanceof Uint8Array) {
                // ArrayBuffer를 문자열로 변환
                const decoder = new TextDecoder('utf-8');
                dataStr = decoder.decode(data);
            } else if (data && data.buffer instanceof ArrayBuffer) {
                // TypedArray 처리 (Uint8Array 등)
                const decoder = new TextDecoder('utf-8');
                dataStr = decoder.decode(data);
            } else {
                // 문자열이거나 다른 타입으로 안전하게 변환
                dataStr = String(data || "");
            }
        } catch (e) {
            console.error("[DCMotor] 데이터 변환 오류:", e);
            dataStr = String(data || "");
        }

        // DC 모터 응답 처리
        if (dataStr.startsWith('MOTOR:PIN:OK')) {
            console.log('[DCMotor] 핀 설정 완료');
        } else if (dataStr.startsWith('MOTOR:SPEED:OK')) {
            const speedParts = dataStr.split(':');
            if (speedParts.length >= 4) {
                this.currentSpeed = parseInt(speedParts[3], 10);
                console.log(`[DCMotor] 속도 설정됨: ${this.currentSpeed}%`);
            }
        } else if (dataStr === 'MOTOR:STOP:OK') {
            this.currentSpeed = 0;
            console.log('[DCMotor] 모터 정지됨');
        } else if (dataStr.startsWith('MOTOR:ERROR:')) {
            const errorMsg = dataStr.substring(12);
            console.error(`[DCMotor] 오류: ${errorMsg}`);
        }
    }
}



/**
 * 자이로센서 클래스
 * SensorBase 상속
 */
class GyroSensor extends SensorBase {
    constructor() {
        super('Gyro', GYRO_CHARACTERISTIC);
        this.x = null;       // X축 가속도
        this.y = null;       // Y축 가속도 
        this.z = null;       // Z축 가속도
        this.roll = null;    // 롤(X축 회전)
        this.pitch = null;   // 피치(Y축 회전)
        this._isStreaming = false; // 스트리밍 상태 추적
        this._streamInterval = 300; // 기본 스트리밍 간격 (ms)
    }

    /**
     * X축 가속도 값 반환
     * @returns {number|null} - X축 가속도 값 또는 null
     */
    getX() {
        return this.x;
    }

    /**
     * Y축 가속도 값 반환
     * @returns {number|null} - Y축 가속도 값 또는 null
     */
    getY() {
        return this.y;
    }

    /**
     * Z축 가속도 값 반환
     * @returns {number|null} - Z축 가속도 값 또는 null
     */
    getZ() {
        return this.z;
    }

    /**
     * 롤 값 반환 (X축 회전)
     * @returns {number|null} - 롤 값(도) 또는 null
     */
    getRoll() {
        return this.roll;
    }

    /**
     * 피치 값 반환 (Y축 회전)
     * @returns {number|null} - 피치 값(도) 또는 null
     */
    getPitch() {
        return this.pitch;
    }

    /**
     * 자이로센서 상태 요청
     * @returns {Promise<boolean>} - 성공 여부
     */
    async getStatus() {
        console.log("자이로센서 상태 요청 전송");
        return await this.sendCommand("GYRO:STATUS");
    }

    /**
     * 자이로센서 핀 설정 (I2C 사용)
     * @param {number} sdaPin - I2C SDA 핀 번호
     * @param {number} sclPin - I2C SCL 핀 번호
     * @returns {Promise<boolean>} - 성공 여부
     */
    async setPin(sdaPin, sclPin) {
        return await this.sendCommand(`GYRO:PIN:${sdaPin},${sclPin}`);
    }

    /**
     * 자이로센서 데이터 처리
     * @param {*} data - 수신 데이터
     */
    _processData(data) {
        if (!data) return;

        console.log("[GyroSensor] 데이터 수신 확인:", data);

        // 데이터 형식 확인 - data.data 구조 처리 추가
        let actualData = data;
        if (data && typeof data === 'object' && data.data !== undefined) {
            console.log("[GyroSensor] data.data 구조 감지, 내부 데이터 사용");
            actualData = data.data;  // 중첩된 구조 처리
        }

        // 데이터 변환 시도
        let dataStr;
        try {
            // ArrayBuffer 또는 DataView인 경우 텍스트로 변환
            if (actualData instanceof ArrayBuffer) {
                const decoder = new TextDecoder('utf-8');
                dataStr = decoder.decode(new DataView(actualData));
                console.log("[GyroSensor] ArrayBuffer에서 변환된 문자열:", dataStr);
            } else if (actualData instanceof DataView) {
                const decoder = new TextDecoder('utf-8');
                dataStr = decoder.decode(actualData);
                console.log("[GyroSensor] DataView에서 변환된 문자열:", dataStr);
            } else if (actualData && actualData.buffer instanceof ArrayBuffer) {
                // TypedArray 처리 (Uint8Array 등)
                const decoder = new TextDecoder('utf-8');
                dataStr = decoder.decode(actualData);
                console.log("[GyroSensor] TypedArray에서 변환된 문자열:", dataStr);
            } else {
                // 문자열이거나 다른 타입으로 안전하게 변환
                dataStr = String(actualData);
                console.log("[GyroSensor] 기본 변환 문자열:", dataStr);
            }
        } catch (e) {
            console.error("[GyroSensor] 데이터 변환 오류:", e);
            dataStr = String(actualData || "");
            console.log("[GyroSensor] 오류 후 강제 변환 문자열:", dataStr);
        }

        // 자이로센서 값 파싱
        try {
            // GYRO:X=123,Y=456,Z=789|ROLL=12.34,PITCH=45.67 형식 처리
            if (dataStr.startsWith("GYRO:")) {
                const dataContent = dataStr.substring(5); // "GYRO:" 제거

                // X, Y, Z 및 ROLL, PITCH 처리
                if (dataContent.includes('|')) {
                    // 가속도와 각도 정보가 | 로 구분된 경우
                    const [accelPart, anglePart] = dataContent.split('|');

                    // 가속도 처리 (X, Y, Z)
                    const accelValues = accelPart.split(',');
                    for (const value of accelValues) {
                        if (value.includes('=')) {
                            const [key, val] = value.split('=');
                            if (key === 'X') this.x = parseFloat(val);
                            else if (key === 'Y') this.y = parseFloat(val);
                            else if (key === 'Z') this.z = parseFloat(val);
                        }
                    }

                    // 각도 처리 (ROLL, PITCH)
                    if (anglePart) {
                        const angleValues = anglePart.split(',');
                        for (const value of angleValues) {
                            if (value.includes('=')) {
                                const [key, val] = value.split('=');
                                if (key === 'ROLL') this.roll = parseFloat(val);
                                else if (key === 'PITCH') this.pitch = parseFloat(val);
                            }
                        }
                    }

                    console.log(`[GyroSensor] 파싱 결과: X=${this.x}, Y=${this.y}, Z=${this.z}, Roll=${this.roll}, Pitch=${this.pitch}`);
                } else {
                    // 단순히 X, Y, Z 값만 있는 경우
                    const values = dataContent.split(',');
                    for (const value of values) {
                        if (value.includes('=')) {
                            const [key, val] = value.split('=');
                            if (key === 'X') this.x = parseFloat(val);
                            else if (key === 'Y') this.y = parseFloat(val);
                            else if (key === 'Z') this.z = parseFloat(val);
                        }
                    }
                    console.log(`[GyroSensor] 파싱 결과: X=${this.x}, Y=${this.y}, Z=${this.z}`);
                }
            }
        } catch (e) {
            console.error("[GyroSensor] 자이로센서 데이터 파싱 오류:", e);
        }
    }

    /**
     * 스트리밍 모드 시작 - 지정된 간격으로 자동 측정
     * @returns {Promise<boolean>} - 성공 여부
     */
    async startStreaming() {
        try {
            this._isStreaming = true;
            console.log("자이로센서 스트리밍 시작");
            return await this.sendCommand('GYRO:STREAM:ON');
        } catch (error) {
            console.error(`[GyroSensor] 스트리밍 시작 실패: ${error.message}`);
            this._isStreaming = false;
            throw error;
        }
    }
    
    /**
     * 스트리밍 모드 중지
     * @returns {Promise<boolean>} - 성공 여부
     */
    async stopStreaming() {
        try {
            this._isStreaming = false;
            console.log("자이로센서 스트리밍 중지");
            return await this.sendCommand('GYRO:STREAM:OFF');
        } catch (error) {
            console.error(`[GyroSensor] 스트리밍 중지 실패: ${error.message}`);
            throw error;
        }
    }
    
    /**
     * 스트리밍 간격 설정
     * @param {number} intervalMs - 간격(ms), 100~5000 사이 값
     * @returns {Promise<boolean>} - 성공 여부
     */
    async setStreamInterval(intervalMs) {
        // 간격 유효성 검사
        if (intervalMs < 100) intervalMs = 100;
        if (intervalMs > 5000) intervalMs = 5000;
        
        try {
            this._streamInterval = intervalMs;
            console.log(`자이로센서 스트리밍 간격 설정: ${intervalMs}ms`);
            return await this.sendCommand(`GYRO:INTERVAL:${intervalMs}`);
        } catch (error) {
            console.error(`[GyroSensor] 스트리밍 간격 설정 실패: ${error.message}`);
            throw error;
        }
    }
    
    /**
     * 현재 스트리밍 상태 확인
     * @returns {boolean} - 스트리밍 중이면 true, 아니면 false
     */
    isStreaming() {
        return this._isStreaming;
    }
}

/**
 * 자이로센서 값 가져오기 함수
 * LightSensor 클래스의 인스턴스에서 값을 읽어옴
 * @param {GyroSensor} sensor - 자이로센서 인스턴스
 * @param {number} maxRetries - 최대 재시도 횟수
 * @param {number} retryDelay - 재시도 지연 시간 (ms)
 * @returns {Promise<Object|null>} - {x, y, z, roll, pitch} 형태의 객체 또는 null
 */
function getGyroSensorValue(sensor, maxRetries = 3, retryDelay = 50) {
    return new Promise((resolve, reject) => {
        // 스트리밍 상태 확인
        if (!sensor.isStreaming()) {
            // 스트리밍이 아니라면 경고 로그
            console.warn("자이로센서가 스트리밍 모드가 아닙니다. 저장된 값이 최신이 아닐 수 있습니다.");
            // 스트리밍 모드가 아니면 getStatus()를 호출하여 최신값 요청
            sensor.getStatus().then(() => {
                // 약간의 지연을 주어 응답을 받을 시간 확보
                setTimeout(attempt, 50);
            }).catch(error => {
                reject(error);
            });
        } else {
            // 스트리밍 모드라면 즉시 저장된 값 확인
            attempt();
        }
        
        let retries = 0;
        
        function attempt() {
            // 저장된 값들이 유효한지 확인
            if (sensor.getX() !== null && sensor.getY() !== null && sensor.getZ() !== null) {
                // 모든 값이 존재하면 객체로 반환
                resolve({
                    x: sensor.getX(),
                    y: sensor.getY(),
                    z: sensor.getZ(),
                    roll: sensor.getRoll(),
                    pitch: sensor.getPitch()
                });
            } else if (retries < maxRetries) {
                // 유효한 값이 없고 재시도 횟수가 남아있으면 재시도
                retries++;
                console.log(`자이로센서 값 가져오기 재시도 (${retries}/${maxRetries})...`);
                setTimeout(attempt, retryDelay);
            } else {
                // 최대 재시도 횟수를 초과하면 오류
                reject(new Error('자이로센서 데이터를 가져올 수 없습니다.'));
            }
        }
    });
}

/**
 * 유효한 자이로센서 값 가져오기 (사용하기 편한 Promise 기반 함수)
 * @param {GyroSensor} sensor - 자이로센서 인스턴스
 * @returns {Promise<Object>} - {x, y, z, roll, pitch} 형태의 객체
 */
async function getValidGyroValue(sensor) {
    if (!sensor) {
        throw new Error("유효한 자이로센서 인스턴스가 필요합니다.");
    }
    
    try {
        // 자이로센서 값 가져오기
        const gyroData = await getGyroSensorValue(sensor);
        return gyroData;
    } catch (error) {
        console.error('Error getting valid gyro value:', error);
        throw error;
    }
}

/**
 * EZMaker 자이로센서 클래스 (ICM20948)
 * SensorBase 상속, EZ_GYRO_CHARACTERISTIC 사용
 */
class EzGyroSensor extends SensorBase {
    constructor() {
        super('EzGyro', EZ_GYRO_CHARACTERISTIC);
        this.ax = null;  // 가속도 X (g)
        this.ay = null;  // 가속도 Y (g)
        this.az = null;  // 가속도 Z (g)
        this.gx = null;  // 자이로 X (dps)
        this.gy = null;  // 자이로 Y (dps)
        this.gz = null;  // 자이로 Z (dps)
        this.roll = null;
        this.pitch = null;
        this.temp = null; // 온도 (℃)
    }

    getAccel() {
        return { x: this.ax, y: this.ay, z: this.az };
    }

    getGyro() {
        return { x: this.gx, y: this.gy, z: this.gz };
    }

    getRoll() {
        return this.roll;
    }

    getPitch() {
        return this.pitch;
    }

    getTemp() {
        return this.temp;
    }

    async getStatus() {
        console.log("EZ자이로센서 상태 요청 전송");
        return await this.sendCommand("EZGYRO:STATUS");
    }

    async setPin(sdaPin, sclPin) {
        return await this.sendCommand(`EZGYRO:PIN:${sdaPin},${sclPin}`);
    }

    _processData(data) {
        if (!data) return;

        console.log("[EzGyroSensor] 데이터 수신 확인:", data);

        let actualData = data;
        if (data && typeof data === 'object' && data.data !== undefined) {
            console.log("[EzGyroSensor] data.data 구조 감지, 내부 데이터 사용");
            actualData = data.data;
        }

        let dataStr;
        try {
            if (actualData instanceof ArrayBuffer) {
                const decoder = new TextDecoder('utf-8');
                dataStr = decoder.decode(new DataView(actualData));
            } else if (actualData instanceof DataView) {
                const decoder = new TextDecoder('utf-8');
                dataStr = decoder.decode(actualData);
            } else if (actualData && actualData.buffer instanceof ArrayBuffer) {
                const decoder = new TextDecoder('utf-8');
                dataStr = decoder.decode(actualData);
            } else {
                dataStr = String(actualData);
            }
        } catch (e) {
            console.error("[EzGyroSensor] 데이터 변환 오류:", e);
            dataStr = String(actualData || "");
        }

        try {
            // EZGYRO:AX=...,AY=...,AZ=...,GX=...,GY=...,GZ=...,ROLL=...,PITCH=...,TEMP=...
            if (dataStr.startsWith("EZGYRO:")) {
                const body = dataStr.substring(7); // "EZGYRO:" 제거
                const parts = body.split(',');
                for (const part of parts) {
                    if (!part.includes('=')) continue;
                    const [key, val] = part.split('=');
                    const f = parseFloat(val);
                    switch (key) {
                        case 'AX': this.ax = f; break;
                        case 'AY': this.ay = f; break;
                        case 'AZ': this.az = f; break;
                        case 'GX': this.gx = f; break;
                        case 'GY': this.gy = f; break;
                        case 'GZ': this.gz = f; break;
                        case 'ROLL': this.roll = f; break;
                        case 'PITCH': this.pitch = f; break;
                        case 'TEMP': this.temp = f; break;
                    }
                }
                console.log(`[EzGyroSensor] 파싱 결과: AX=${this.ax}, AY=${this.ay}, AZ=${this.az}, GX=${this.gx}, GY=${this.gy}, GZ=${this.gz}, ROLL=${this.roll}, PITCH=${this.pitch}, TEMP=${this.temp}`);
            }
        } catch (e) {
            console.error("[EzGyroSensor] 데이터 파싱 오류:", e);
        }
    }
}

/**
 * EZ자이로센서 값 가져오기 함수
 * @param {EzGyroSensor} sensor - EZ자이로센서 인스턴스
 * @param {number} maxRetries - 최대 재시도 횟수
 * @param {number} retryDelay - 재시도 지연 시간 (ms)
 * @returns {Promise<Object|null>} - {ax, ay, az, gx, gy, gz, roll, pitch, temp} 형태의 객체 또는 null
 */
function getEzGyroSensorValue(sensor, maxRetries = 3, retryDelay = 50) {
    return new Promise((resolve, reject) => {
        let retries = 0;

        function attempt() {
            const accel = sensor.getAccel();
            const gyro  = sensor.getGyro();
            const roll  = sensor.getRoll();
            const pitch = sensor.getPitch();
            const temp  = sensor.getTemp();

            const hasData =
                accel && (accel.x != null || accel.y != null || accel.z != null) ||
                gyro  && (gyro.x  != null || gyro.y  != null || gyro.z  != null);

            if (hasData) {
                resolve({
                    ax: accel.x, ay: accel.y, az: accel.z,
                    gx: gyro.x,  gy: gyro.y,  gz: gyro.z,
                    roll, pitch, temp
                });
            } else if (retries < maxRetries) {
                retries++;
                console.log(`EZGyro 값이 아직 없습니다. 재시도 ${retries}/${maxRetries}`);
                sensor.getStatus().then(() => {
                    setTimeout(attempt, retryDelay);
                }).catch(error => {
                    reject(error);
                });
            } else {
                reject(new Error('EZ자이로센서 데이터를 가져올 수 없습니다.'));
            }
        }

        // 최초 시도
        sensor.getStatus().then(() => {
            setTimeout(attempt, retryDelay);
        }).catch(error => {
            reject(error);
        });
    });
}

/**
 * EZ자이로센서 유효값 가져오기 (Promise 기반)
 * @param {EzGyroSensor} sensor
 * @returns {Promise<Object>} - {ax, ay, az, gx, gy, gz, roll, pitch, temp}
 */
async function getValidEzGyroValue(sensor) {
    if (!sensor) {
        throw new Error("유효한 EzGyroSensor 인스턴스가 필요합니다.");
    }
    return await getEzGyroSensorValue(sensor);
}

/**
 * EZ자이로 센서 값 캐시 보장 함수
 * - maxAgeMs 이내면 마지막으로 읽은 값을 재사용
 * - maxAgeMs 를 초과하면 getValidEzGyroValue(sensor)로 다시 측정하여 캐시 갱신
 *
 * 블록을 여러 개로 나눌 때, 같은 실행 흐름(짧은 시간) 안에서는 "한 번만 측정"하고
 * 각 블록은 동일한 샘플을 공유하도록 하기 위한 용도입니다.
 *
 * @param {EzGyroSensor} sensor
 * @param {number} maxAgeMs - 캐시 유효시간(ms), 기본 200ms
 * @returns {Promise<{ax, ay, az, gx, gy, gz, roll, pitch, temp}>}
 */
async function ensureEzGyroCache(sensor, maxAgeMs = 200) {
    if (!sensor) {
        throw new Error("유효한 EzGyroSensor 인스턴스가 필요합니다.");
    }

    const now = Date.now();
    const ts = window.__ezGyroCacheTs;
    const hasValidTs = (typeof ts === 'number' && !isNaN(ts));

    if (!window.__ezGyroCache || !hasValidTs || (now - ts) >= maxAgeMs) {
        window.__ezGyroCache = await getValidEzGyroValue(sensor);
        window.__ezGyroCacheTs = now;
    }

    return window.__ezGyroCache;
}

/**
 * EZ자이로 캐시 초기화(선택)
 */
function clearEzGyroCache() {
    window.__ezGyroCache = null;
    window.__ezGyroCacheTs = 0;
}

/**
 * EZMaker CO2 센서 클래스 (SCD40, EZCO2)
 * SensorBase 상속, EZ_CO2_CHARACTERISTIC 사용
 */
class EzCo2Sensor extends SensorBase {
    constructor() {
        super('EzCo2', EZ_CO2_CHARACTERISTIC);
        this.co2 = null;       // CO2 농도 (ppm)
        this.temp = null;      // 온도 (℃)
        this.humidity = null;  // 습도 (%RH)
    }

    getCo2() {
        return this.co2;
    }

    getTemp() {
        return this.temp;
    }

    getHumidity() {
        return this.humidity;
    }

    async getStatus() {
        console.log("EZCO2 센서 상태 요청 전송");
        return await this.sendCommand("EZCO2:STATUS");
    }

    async setPin(sdaPin, sclPin) {
        return await this.sendCommand(`EZCO2:PIN:${sdaPin},${sclPin}`);
    }

    _processData(data) {
        if (!data) return;

        console.log("[EzCo2Sensor] 데이터 수신 확인:", data);

        let actualData = data;
        if (data && typeof data === 'object' && data.data !== undefined) {
            console.log("[EzCo2Sensor] data.data 구조 감지, 내부 데이터 사용");
            actualData = data.data;
        }

        let dataStr;
        try {
            if (actualData instanceof ArrayBuffer) {
                const decoder = new TextDecoder('utf-8');
                dataStr = decoder.decode(new DataView(actualData));
            } else if (actualData instanceof DataView) {
                const decoder = new TextDecoder('utf-8');
                dataStr = decoder.decode(actualData);
            } else if (actualData && actualData.buffer instanceof ArrayBuffer) {
                const decoder = new TextDecoder('utf-8');
                dataStr = decoder.decode(actualData);
            } else {
                dataStr = String(actualData);
            }
        } catch (e) {
            console.error("[EzCo2Sensor] 데이터 변환 오류:", e);
            dataStr = String(actualData || "");
        }

        try {
            // EZCO2:CO2=...,T=...,H=...
            if (dataStr.startsWith("EZCO2:")) {
                const body = dataStr.substring(6); // "EZCO2:" 제거
                const parts = body.split(',');
                for (const part of parts) {
                    if (!part.includes('=')) continue;
                    const [key, val] = part.split('=');
                    const f = parseFloat(val);
                    switch (key) {
                        case 'CO2': this.co2 = f; break;
                        case 'T':   this.temp = f; break;
                        case 'H':   this.humidity = f; break;
                    }
                }
                console.log(`[EzCo2Sensor] 파싱 결과: CO2=${this.co2}, T=${this.temp}, H=${this.humidity}`);
            }
        } catch (e) {
            console.error("[EzCo2Sensor] 데이터 파싱 오류:", e);
        }
    }
}

/**
 * EZCO2 센서 값 가져오기 함수
 * @param {EzCo2Sensor} sensor - EZCO2 센서 인스턴스
 * @param {number} maxRetries - 최대 재시도 횟수
 * @param {number} retryDelay - 재시도 지연 시간 (ms)
 * @returns {Promise<Object|null>} - {co2, temp, humidity} 형태의 객체 또는 null
 */
function getEzCo2SensorValue(sensor, maxRetries = 3, retryDelay = 500) {
    return new Promise((resolve, reject) => {
        let retries = 0;

        function attempt() {
            const co2  = sensor.getCo2();
            const temp = sensor.getTemp();
            const hum  = sensor.getHumidity();

            const hasData = (co2 != null);

            if (hasData) {
                resolve({
                    co2,
                    temp,
                    humidity: hum,
                });
            } else if (retries < maxRetries) {
                retries++;
                console.log(`EZCO2 값이 아직 없습니다. 재시도 ${retries}/${maxRetries}`);
                sensor.getStatus().then(() => {
                    setTimeout(attempt, retryDelay);
                }).catch(error => {
                    reject(error);
                });
            } else {
                reject(new Error('EZCO2 센서 데이터를 가져올 수 없습니다.'));
            }
        }

        // 최초 시도
        sensor.getStatus().then(() => {
            setTimeout(attempt, retryDelay);
        }).catch(error => {
            reject(error);
        });
    });
}

/**
 * EZCO2 센서 유효값 가져오기 (Promise 기반)
 * @param {EzCo2Sensor} sensor
 * @returns {Promise<Object>} - {co2, temp, humidity}
 */
async function getValidEzCo2Value(sensor) {
    if (!sensor) {
        throw new Error("유효한 EzCo2Sensor 인스턴스가 필요합니다.");
    }
    return await getEzCo2SensorValue(sensor);
}

/**
 * EZMaker DIY-A 전자기 유도 센서 클래스 (DIY-A)
 * SensorBase 상속, DIYA_CHARACTERISTIC 사용
 */
class DiyASensor extends SensorBase {
    constructor() {
        super('DiyA', DIYA_CHARACTERISTIC);
        this.raw = null;      // 10비트 Raw 값 (0~1023)
        this.voltage = null;  // 0~5V 환산 전압
    }

    getRaw() {
        return this.raw;
    }

    getVoltage() {
        return this.voltage;
    }

    async getStatus() {
        console.log("DIY-A 센서 상태 요청 전송");
        return await this.sendCommand("DIYA:STATUS");
    }

    async setPin(adcPin) {
        // EZMaker 보드의 A0/A1 등과 매핑되는 GPIO 번호를 그대로 사용
        return await this.sendCommand(`DIYA:PIN:${adcPin}`);
    }

    _processData(data) {
        if (!data) return;

        console.log("[DiyASensor] 데이터 수신 확인:", data);

        let actualData = data;
        if (data && typeof data === 'object' && data.data !== undefined) {
            console.log("[DiyASensor] data.data 구조 감지, 내부 데이터 사용");
            actualData = data.data;
        }

        let dataStr;
        try {
            if (actualData instanceof ArrayBuffer) {
                const decoder = new TextDecoder('utf-8');
                dataStr = decoder.decode(new DataView(actualData));
            } else if (actualData instanceof DataView) {
                const decoder = new TextDecoder('utf-8');
                dataStr = decoder.decode(actualData);
            } else if (actualData && actualData.buffer instanceof ArrayBuffer) {
                const decoder = new TextDecoder('utf-8');
                dataStr = decoder.decode(actualData);
            } else {
                dataStr = String(actualData);
            }
        } catch (e) {
            console.error("[DiyASensor] 데이터 변환 오류:", e);
            dataStr = String(actualData || "");
        }

        try {
            // 펌웨어 포맷: "DIYA:<voltage>,<raw>" (예: DIYA:1.234,512)
            if (dataStr.startsWith("DIYA:")) {
                const body = dataStr.substring(5);
                const parts = body.split(',');
                if (parts.length >= 2) {
                    const v = parseFloat(parts[0]);
                    const r = parseInt(parts[1], 10);
                    if (!isNaN(v)) {
                        this.voltage = v;
                    }
                    if (!isNaN(r)) {
                        this.raw = r;
                    }
                    console.log(`[DiyASensor] 파싱 결과: voltage=${this.voltage}, raw=${this.raw}`);
                }
            }
        } catch (e) {
            console.error("[DiyASensor] 데이터 파싱 오류:", e);
        }
    }
}

/**
 * EZMaker DIY-B 전류/전도도 센서 클래스 (DIY-B)
 * SensorBase 상속, DIYB_CHARACTERISTIC 사용
 */
class DiyBSensor extends SensorBase {
    constructor() {
        super('DiyB', DIYB_CHARACTERISTIC);
        this.raw = null;      // 10비트 Raw 값 (0~1023)
        this.voltage = null;  // 0~5V 환산 전압
    }

    getRaw() {
        return this.raw;
    }

    getVoltage() {
        return this.voltage;
    }

    async getStatus() {
        console.log("DIY-B 센서 상태 요청 전송");
        return await this.sendCommand("DIYB:STATUS");
    }

    async setPin(adcPin) {
        // EZMaker 보드의 A1 등과 매핑되는 GPIO 번호를 그대로 사용
        return await this.sendCommand(`DIYB:PIN:${adcPin}`);
    }

    _processData(data) {
        if (!data) return;

        console.log("[DiyBSensor] 데이터 수신 확인:", data);

        let actualData = data;
        if (data && typeof data === 'object' && data.data !== undefined) {
            console.log("[DiyBSensor] data.data 구조 감지, 내부 데이터 사용");
            actualData = data.data;
        }

        let dataStr;
        try {
            if (actualData instanceof ArrayBuffer) {
                const decoder = new TextDecoder('utf-8');
                dataStr = decoder.decode(new DataView(actualData));
            } else if (actualData instanceof DataView) {
                const decoder = new TextDecoder('utf-8');
                dataStr = decoder.decode(actualData);
            } else if (actualData && actualData.buffer instanceof ArrayBuffer) {
                const decoder = new TextDecoder('utf-8');
                dataStr = decoder.decode(actualData);
            } else {
                dataStr = String(actualData);
            }
        } catch (e) {
            console.error("[DiyBSensor] 데이터 변환 오류:", e);
            dataStr = String(actualData || "");
        }

        try {
            // 펌웨어 포맷: "DIYB:<voltage>,<raw>" (예: DIYB:1.234,512)
            if (dataStr.startsWith("DIYB:")) {
                const body = dataStr.substring(5);
                const parts = body.split(',');
                if (parts.length >= 2) {
                    const v = parseFloat(parts[0]);
                    const r = parseInt(parts[1], 10);
                    if (!isNaN(v)) {
                        this.voltage = v;
                    }
                    if (!isNaN(r)) {
                        this.raw = r;
                    }
                    console.log(`[DiyBSensor] 파싱 결과: voltage=${this.voltage}, raw=${this.raw}`);
                }
            }
        } catch (e) {
            console.error("[DiyBSensor] 데이터 파싱 오류:", e);
        }
    }
}

/**
 * EZMaker 자기장(Hall) 센서 클래스
 * SensorBase 상속, HALL_CHARACTERISTIC 사용
 */
class HallSensor extends SensorBase {
    constructor() {
        super('Hall', HALL_CHARACTERISTIC);
        this.raw = null;       // 10비트 Raw 값 (0~1023)
        this.strength = null;  // N/S 세기 (-512 ~ +512)
        this.density = null;   // 자속 밀도 (0 ~ 512)
    }

    getRaw() {
        return this.raw;
    }

    getStrength() {
        return this.strength;
    }

    getDensity() {
        return this.density;
    }

    async getStatus() {
        console.log("Hall 센서 상태 요청 전송");
        return await this.sendCommand("HALL:STATUS");
    }

    async setPin(adcPin) {
        // EZMaker 보드의 A0/A1 등과 매핑되는 GPIO 번호를 그대로 사용
        return await this.sendCommand(`HALL:PIN:${adcPin}`);
    }

    _processData(data) {
        if (!data) return;

        console.log("[HallSensor] 데이터 수신 확인:", data);

        let actualData = data;
        if (data && typeof data === 'object' && data.data !== undefined) {
            console.log("[HallSensor] data.data 구조 감지, 내부 데이터 사용");
            actualData = data.data;
        }

        let dataStr;
        try {
            if (actualData instanceof ArrayBuffer) {
                const decoder = new TextDecoder('utf-8');
                dataStr = decoder.decode(new DataView(actualData));
            } else if (actualData instanceof DataView) {
                const decoder = new TextDecoder('utf-8');
                dataStr = decoder.decode(actualData);
            } else if (actualData && actualData.buffer instanceof ArrayBuffer) {
                const decoder = new TextDecoder('utf-8');
                dataStr = decoder.decode(actualData);
            } else {
                dataStr = String(actualData);
            }
        } catch (e) {
            console.error("[HallSensor] 데이터 변환 오류:", e);
            dataStr = String(actualData || "");
        }

        try {
            // 펌웨어 포맷: "HALL:<raw>,<strength>,<density>"
            if (dataStr.startsWith("HALL:")) {
                const body = dataStr.substring(5);
                const parts = body.split(',');
                if (parts.length >= 3) {
                    const r = parseInt(parts[0], 10);
                    const s = parseInt(parts[1], 10);
                    const d = parseInt(parts[2], 10);
                    if (!isNaN(r)) this.raw = r;
                    if (!isNaN(s)) this.strength = s;
                    if (!isNaN(d)) this.density = d;
                    console.log(`[HallSensor] 파싱 결과: raw=${this.raw}, strength=${this.strength}, density=${this.density}`);
                }
            }
        } catch (e) {
            console.error("[HallSensor] 데이터 파싱 오류:", e);
        }
    }
}

/**
 * EZMaker 밝기센서(EZLIGHT) 클래스
 * SensorBase 상속, EZ_LIGHT_CHARACTERISTIC 사용
 */
class EzLightSensor extends SensorBase {
    constructor() {
        super('EzLight', EZ_LIGHT_CHARACTERISTIC);
        this.raw = null;      // 10비트 Raw 값 (0~1023)
        this.percent = null;  // 밝기 비율 (0~100 %)
    }

    getRaw() {
        return this.raw;
    }

    getPercent() {
        return this.percent;
    }

    async getStatus() {
        console.log("EZLIGHT 센서 상태 요청 전송");
        return await this.sendCommand("EZLIGHT:STATUS");
    }

    async setPin(adcPin) {
        // EZMaker 보드의 A0/A1 등과 매핑되는 GPIO 번호를 그대로 사용
        return await this.sendCommand(`EZLIGHT:PIN:${adcPin}`);
    }

    _processData(data) {
        if (!data) return;

        console.log("[EzLightSensor] 데이터 수신 확인:", data);

        let actualData = data;
        if (data && typeof data === 'object' && data.data !== undefined) {
            console.log("[EzLightSensor] data.data 구조 감지, 내부 데이터 사용");
            actualData = data.data;
        }

        let dataStr;
        try {
            if (actualData instanceof ArrayBuffer) {
                const decoder = new TextDecoder('utf-8');
                dataStr = decoder.decode(new DataView(actualData));
            } else if (actualData instanceof DataView) {
                const decoder = new TextDecoder('utf-8');
                dataStr = decoder.decode(actualData);
            } else if (actualData && actualData.buffer instanceof ArrayBuffer) {
                const decoder = new TextDecoder('utf-8');
                dataStr = decoder.decode(actualData);
            } else {
                dataStr = String(actualData);
            }
        } catch (e) {
            console.error("[EzLightSensor] 데이터 변환 오류:", e);
            dataStr = String(actualData || "");
        }

        try {
            // 펌웨어 포맷: "EZLIGHT:<raw>,<percent>"
            if (dataStr.startsWith("EZLIGHT:")) {
                const body = dataStr.substring(8);
                const parts = body.split(',');
                if (parts.length >= 2) {
                    const r = parseInt(parts[0], 10);
                    const p = parseFloat(parts[1]);
                    if (!isNaN(r)) this.raw = r;
                    if (!isNaN(p)) this.percent = p;
                    console.log(`[EzLightSensor] 파싱 결과: raw=${this.raw}, percent=${this.percent}`);
                }
            }
        } catch (e) {
            console.error("[EzLightSensor] 데이터 파싱 오류:", e);
        }
    }
}

/**
 * EZMaker 전압센서(EZVOLT) 클래스
 * SensorBase 상속, EZ_VOLT_CHARACTERISTIC 사용
 */
class EzVoltSensor extends SensorBase {
    constructor() {
        super('EzVolt', EZ_VOLT_CHARACTERISTIC);
        this.raw = null;      // 10비트 Raw 값 (0~1023)
        this.voltage = null;  // 입력 전압 (0~25V 환산)
    }

    getRaw() {
        return this.raw;
    }

    getVoltage() {
        return this.voltage;
    }

    async getStatus() {
        console.log("EZVOLT 센서 상태 요청 전송");
        return await this.sendCommand("EZVOLT:STATUS");
    }

    async setPin(adcPin) {
        // EZMaker 보드의 A0/A1 등과 매핑되는 GPIO 번호를 그대로 사용
        return await this.sendCommand(`EZVOLT:PIN:${adcPin}`);
    }

    _processData(data) {
        if (!data) return;

        console.log("[EzVoltSensor] 데이터 수신 확인:", data);

        let actualData = data;
        if (data && typeof data === 'object' && data.data !== undefined) {
            console.log("[EzVoltSensor] data.data 구조 감지, 내부 데이터 사용");
            actualData = data.data;
        }

        let dataStr;
        try {
            if (actualData instanceof ArrayBuffer) {
                const decoder = new TextDecoder('utf-8');
                dataStr = decoder.decode(new DataView(actualData));
            } else if (actualData instanceof DataView) {
                const decoder = new TextDecoder('utf-8');
                dataStr = decoder.decode(actualData);
            } else if (actualData && actualData.buffer instanceof ArrayBuffer) {
                const decoder = new TextDecoder('utf-8');
                dataStr = decoder.decode(actualData);
            } else {
                dataStr = String(actualData);
            }
        } catch (e) {
            console.error("[EzVoltSensor] 데이터 변환 오류:", e);
            dataStr = String(actualData || "");
        }

        try {
            // 펌웨어 포맷: "EZVOLT:<raw>,<voltage>"
            if (dataStr.startsWith("EZVOLT:")) {
                const body = dataStr.substring(7);
                const parts = body.split(',');
                if (parts.length >= 2) {
                    const r = parseInt(parts[0], 10);
                    const v = parseFloat(parts[1]);
                    if (!isNaN(r)) this.raw = r;
                    if (!isNaN(v)) this.voltage = v;
                    console.log(`[EzVoltSensor] 파싱 결과: raw=${this.raw}, voltage=${this.voltage}`);
                }
            }
        } catch (e) {
            console.error("[EzVoltSensor] 데이터 파싱 오류:", e);
        }
    }
}

/**
 * EZMaker 전류센서(EZCURR, INA219) 클래스
 * SensorBase 상속, EZ_CURR_CHARACTERISTIC 사용
 */
class EzCurrSensor extends SensorBase {
    constructor() {
        super('EzCurr', EZ_CURR_CHARACTERISTIC);
        this.current_mA = null; // 전류 (mA)
        this.voltage = null;    // 버스 전압 (V)
        this.power_mW = null;   // 전력 (mW) - 펌웨어에서 보낼 경우 사용
    }

    getCurrent() {
        return this.current_mA;
    }

    getVoltage() {
        return this.voltage;
    }

    getPower() {
        return this.power_mW;
    }

    async getStatus() {
        console.log("EZCURR 센서 상태 요청 전송");
        return await this.sendCommand("EZCURR:STATUS");
    }

    async setPin(sdaPin, sclPin) {
        // EZMaker 보드의 I2C SDA/SCL 핀 번호를 그대로 사용
        return await this.sendCommand(`EZCURR:PIN:${sdaPin},${sclPin}`);
    }

    _processData(data) {
        if (!data) return;

        console.log("[EzCurrSensor] 데이터 수신 확인:", data);

        let actualData = data;
        if (data && typeof data === 'object' && data.data !== undefined) {
            console.log("[EzCurrSensor] data.data 구조 감지, 내부 데이터 사용");
            actualData = data.data;
        }

        let dataStr;
        try {
            if (actualData instanceof ArrayBuffer) {
                const decoder = new TextDecoder('utf-8');
                dataStr = decoder.decode(new DataView(actualData));
            } else if (actualData instanceof DataView) {
                const decoder = new TextDecoder('utf-8');
                dataStr = decoder.decode(actualData);
            } else if (actualData && actualData.buffer instanceof ArrayBuffer) {
                const decoder = new TextDecoder('utf-8');
                dataStr = decoder.decode(actualData);
            } else {
                dataStr = String(actualData);
            }
        } catch (e) {
            console.error("[EzCurrSensor] 데이터 변환 오류:", e);
            dataStr = String(actualData || "");
        }

        try {
            // 펌웨어 포맷: "EZCURR:<current_mA>,<voltage_V>"
            if (dataStr.startsWith("EZCURR:")) {
                const body = dataStr.substring(7);
                const parts = body.split(',');
                if (parts.length >= 2) {
                    const i = parseFloat(parts[0]);
                    const v = parseFloat(parts[1]);
                    if (!isNaN(i)) this.current_mA = i;
                    if (!isNaN(v)) this.voltage = v;
                    console.log(`[EzCurrSensor] 파싱 결과: current=${this.current_mA}mA, voltage=${this.voltage}V`);
                }
            }
        } catch (e) {
            console.error("[EzCurrSensor] 데이터 파싱 오류:", e);
        }
    }
}

/**
 * EZMaker 수중/접촉 온도센서(EZTHERMAL, DS18B20) 클래스
 * SensorBase 상속, EZ_THERMAL_CHARACTERISTIC 사용
 */
class EzThermalSensor extends SensorBase {
    constructor() {
        super('EzThermal', EZ_THERMAL_CHARACTERISTIC);
        this.temperature = null;  // 현재 온도 (℃)
    }

    /**
     * 현재 온도 값(℃) 반환
     * @returns {number|null}
     */
    getTemperature() {
        return this.temperature;
    }

    /**
     * 상태 요청 (EZTHERMAL:STATUS)
     * @returns {Promise<boolean>}
     */
    async getStatus() {
        console.log("EZTHERMAL 센서 상태 요청 전송");
        return await this.sendCommand("EZTHERMAL:STATUS");
    }

    /**
     * 센서 핀 설정 (디지털 데이터 핀)
     * @param {number} pin - GPIO 번호 (예: EZMaker D0 → GPIO 21)
     * @returns {Promise<boolean>}
     */
    async setPin(pin) {
        return await this.sendCommand(`EZTHERMAL:PIN:${pin}`);
    }

    /**
     * 데이터 처리
     * @param {*} data - 수신 데이터
     */
    _processData(data) {
        if (!data) return;

        console.log("[EzThermalSensor] 데이터 수신 확인:", data);

        let actualData = data;
        if (data && typeof data === 'object' && data.data !== undefined) {
            console.log("[EzThermalSensor] data.data 구조 감지, 내부 데이터 사용");
            actualData = data.data;
        }

        let dataStr;
        try {
            if (actualData instanceof ArrayBuffer) {
                const decoder = new TextDecoder('utf-8');
                dataStr = decoder.decode(new DataView(actualData));
            } else if (actualData instanceof DataView) {
                const decoder = new TextDecoder('utf-8');
                dataStr = decoder.decode(actualData);
            } else if (actualData && actualData.buffer instanceof ArrayBuffer) {
                const decoder = new TextDecoder('utf-8');
                dataStr = decoder.decode(actualData);
            } else {
                dataStr = String(actualData);
            }
        } catch (e) {
            console.error("[EzThermalSensor] 데이터 변환 오류:", e);
            dataStr = String(actualData || "");
        }

        try {
            // 펌웨어 포맷: "EZTHERMAL:<temperatureC>"
            if (dataStr.startsWith("EZTHERMAL:")) {
                const body = dataStr.substring("EZTHERMAL:".length);
                const t = parseFloat(body);
                if (!isNaN(t)) {
                    this.temperature = t;
                    console.log(`[EzThermalSensor] 파싱 결과: temperature=${this.temperature} °C`);
                }
            }
        } catch (e) {
            console.error("[EzThermalSensor] 데이터 파싱 오류:", e);
        }
    }
}

/**
 * EZMaker 소리센서(EZSOUND) 클래스
 * SensorBase 상속, EZ_SOUND_CHARACTERISTIC 사용
 */
class EzSoundSensor extends SensorBase {
    constructor() {
        super('EzSound', EZ_SOUND_CHARACTERISTIC);
        this.raw = null;      // 10비트 Raw 값 (0~1023)
        this.percent = null;  // 소리 레벨 비율 (0~100 %)
    }

    getRaw() {
        return this.raw;
    }

    getPercent() {
        return this.percent;
    }

    async getStatus() {
        console.log("EZSOUND 센서 상태 요청 전송");
        return await this.sendCommand("EZSOUND:STATUS");
    }

    async setPin(adcPin) {
        // EZMaker 보드의 A0~A4 포트에 대응하는 GPIO 번호를 그대로 사용
        return await this.sendCommand(`EZSOUND:PIN:${adcPin}`);
    }

    _processData(data) {
        if (!data) return;

        console.log("[EzSoundSensor] 데이터 수신 확인:", data);

        let actualData = data;
        if (data && typeof data === 'object' && data.data !== undefined) {
            console.log("[EzSoundSensor] data.data 구조 감지, 내부 데이터 사용");
            actualData = data.data;
        }

        let dataStr;
        try {
            if (actualData instanceof ArrayBuffer) {
                const decoder = new TextDecoder('utf-8');
                dataStr = decoder.decode(new DataView(actualData));
            } else if (actualData instanceof DataView) {
                const decoder = new TextDecoder('utf-8');
                dataStr = decoder.decode(actualData);
            } else if (actualData && actualData.buffer instanceof ArrayBuffer) {
                const decoder = new TextDecoder('utf-8');
                dataStr = decoder.decode(actualData);
            } else {
                dataStr = String(actualData);
            }
        } catch (e) {
            console.error("[EzSoundSensor] 데이터 변환 오류:", e);
            dataStr = String(actualData || "");
        }

        try {
            // 펌웨어 포맷: "EZSOUND:<raw>,<percent>"
            if (dataStr.startsWith("EZSOUND:")) {
                const body = dataStr.substring("EZSOUND:".length);
                const parts = body.split(',');
                if (parts.length >= 2) {
                    const r = parseInt(parts[0], 10);
                    const p = parseFloat(parts[1]);
                    if (!isNaN(r)) this.raw = r;
                    if (!isNaN(p)) this.percent = p;
                    console.log(`[EzSoundSensor] 파싱 결과: raw=${this.raw}, percent=${this.percent}`);
                }
            }
        } catch (e) {
            console.error("[EzSoundSensor] 데이터 파싱 오류:", e);
        }
    }
}

/**
 * EZMaker 무게센서(EZWEIGHT, HX711) 클래스
 * SensorBase 상속, EZ_WEIGHT_CHARACTERISTIC 사용
 */
class EzWeightSensor extends SensorBase {
    constructor() {
        super('EzWeight', EZ_WEIGHT_CHARACTERISTIC);
        this.raw = null;     // HX711 Raw 카운트 값
        this.weight = null;  // 보정된 무게 값 (g 단위 가정)
    }

    getRaw() {
        return this.raw;
    }

    getWeight() {
        return this.weight;
    }

    async getStatus() {
        console.log("EZWEIGHT 센서 상태 요청 전송");
        return await this.sendCommand("EZWEIGHT:STATUS");
    }

    async setPin(doutPin, sckPin) {
        // HX711 DOUT(DT), SCK(CLK) 핀 조합 사용
        return await this.sendCommand(`EZWEIGHT:PIN:${doutPin},${sckPin}`);
    }

    _processData(data) {
        if (!data) return;

        console.log("[EzWeightSensor] 데이터 수신 확인:", data);

        let actualData = data;
        if (data && typeof data === 'object' && data.data !== undefined) {
            console.log("[EzWeightSensor] data.data 구조 감지, 내부 데이터 사용");
            actualData = data.data;
        }

        let dataStr;
        try {
            if (actualData instanceof ArrayBuffer) {
                const decoder = new TextDecoder('utf-8');
                dataStr = decoder.decode(new DataView(actualData));
            } else if (actualData instanceof DataView) {
                const decoder = new TextDecoder('utf-8');
                dataStr = decoder.decode(actualData);
            } else if (actualData && actualData.buffer instanceof ArrayBuffer) {
                const decoder = new TextDecoder('utf-8');
                dataStr = decoder.decode(actualData);
            } else {
                dataStr = String(actualData);
            }
        } catch (e) {
            console.error("[EzWeightSensor] 데이터 변환 오류:", e);
            dataStr = String(actualData || "");
        }

        try {
            // 펌웨어 포맷: "EZWEIGHT:<raw>,<weight>"
            if (dataStr.startsWith("EZWEIGHT:")) {
                const body = dataStr.substring("EZWEIGHT:".length);
                const parts = body.split(',');
                if (parts.length >= 2) {
                    const r = parseInt(parts[0], 10);
                    const w = parseFloat(parts[1]);
                    if (!isNaN(r)) this.raw = r;
                    if (!isNaN(w)) this.weight = w;
                    console.log(`[EzWeightSensor] 파싱 결과: raw=${this.raw}, weight=${this.weight}`);
                }
            }
        } catch (e) {
            console.error("[EzWeightSensor] 데이터 파싱 오류:", e);
        }
    }
}

/**
 * EZMaker 미세먼지 센서(EZDUST, PMS7003M) 클래스
 * SensorBase 상속, EZ_DUST_CHARACTERISTIC 사용
 *
 * 펌웨어 응답 포맷:
 *   "EZDUST:PM10,PM2.5,PM1.0"
 *   (모두 μg/m³)
 */
class EzDustSensor extends SensorBase {
    constructor() {
        super('EzDust', EZ_DUST_CHARACTERISTIC);
        this.pm10  = null; // 미세먼지 (PM10)
        this.pm2_5 = null; // 초미세먼지 (PM2.5)
        this.pm1_0 = null; // 극초미세먼지 (PM1.0)
    }

    getPm10() {
        return this.pm10;
    }

    getPm2_5() {
        return this.pm2_5;
    }

    getPm1_0() {
        return this.pm1_0;
    }

    async getStatus() {
        console.log("EZDUST 센서 상태 요청 전송");
        return await this.sendCommand("EZDUST:STATUS");
    }

    /**
     * UART 핀 설정
     * @param {number} rxPin - 보드 RX (센서 TX에 연결)
     * @param {number} txPin - 보드 TX (센서 RX에 연결)
     */
    async setPin(rxPin, txPin) {
        return await this.sendCommand(`EZDUST:PIN:${rxPin},${txPin}`);
    }

    _processData(data) {
        if (!data) return;

        console.log("[EzDustSensor] 데이터 수신 확인:", data);

        let actualData = data;
        if (data && typeof data === 'object' && data.data !== undefined) {
            console.log("[EzDustSensor] data.data 구조 감지, 내부 데이터 사용");
            actualData = data.data;
        }

        let dataStr;
        try {
            if (actualData instanceof ArrayBuffer) {
                const decoder = new TextDecoder('utf-8');
                dataStr = decoder.decode(new DataView(actualData));
            } else if (actualData instanceof DataView) {
                const decoder = new TextDecoder('utf-8');
                dataStr = decoder.decode(actualData);
            } else if (actualData && actualData.buffer instanceof ArrayBuffer) {
                const decoder = new TextDecoder('utf-8');
                dataStr = decoder.decode(actualData);
            } else {
                dataStr = String(actualData);
            }
        } catch (e) {
            console.error("[EzDustSensor] 데이터 변환 오류:", e);
            dataStr = String(actualData || "");
        }

        try {
            // 펌웨어 포맷: "EZDUST:PM10,PM2.5,PM1.0"
            if (dataStr.startsWith("EZDUST:")) {
                const body = dataStr.substring("EZDUST:".length);
                const parts = body.split(',');
                if (parts.length >= 3) {
                    const pm10  = parseFloat(parts[0]);
                    const pm2_5 = parseFloat(parts[1]);
                    const pm1_0 = parseFloat(parts[2]);

                    if (!isNaN(pm10))  this.pm10  = pm10;
                    if (!isNaN(pm2_5)) this.pm2_5 = pm2_5;
                    if (!isNaN(pm1_0)) this.pm1_0 = pm1_0;

                    console.log(`[EzDustSensor] 파싱 결과: PM10=${this.pm10}, PM2.5=${this.pm2_5}, PM1.0=${this.pm1_0}`);
                }
            }
        } catch (e) {
            console.error("[EzDustSensor] 데이터 파싱 오류:", e);
        }
    }
}

/**
 * I2C LCD (16x2 / 20x4) 디스플레이 클래스
 * SensorBase 상속, LCD_CHARACTERISTIC 사용
 */
class LcdDisplay extends SensorBase {
    constructor() {
        super('LCD', LCD_CHARACTERISTIC);
        this.type = null;  // "16X2" 또는 "20X4"
        this.rows = 0;
        this.cols = 0;
        this.sclPin = null;
        this.sdaPin = null;
    }

    /**
     * LCD 초기화
     * @param {string} type - "16X2" 또는 "20X4"
     * @param {number} sclPin - I2C SCL 핀 번호 (예: 40)
     * @param {number} sdaPin - I2C SDA 핀 번호 (예: 41)
     * @returns {Promise<boolean>}
     */
    async init(type = "16X2", sclPin = 40, sdaPin = 41) {
        const upperType = (type || "16X2").toUpperCase();

        // 내부 상태 저장
        this.type = upperType;
        if (upperType === "20X4") {
            this.cols = 20;
            this.rows = 4;
        } else {
            this.cols = 16;
            this.rows = 2;
        }
        this.sclPin = sclPin;
        this.sdaPin = sdaPin;

        const cmd = `LCD:INIT:${upperType}:${sclPin},${sdaPin}`;
        return await this.sendCommand(cmd);
    }

    /**
     * 화면 클리어
     * @returns {Promise<boolean>}
     */
    async clear() {
        return await this.sendCommand("LCD:CLEAR");
    }

    /**
     * 백라이트 설정
     * @param {boolean} on - true 이면 ON, false 이면 OFF
     * @returns {Promise<boolean>}
     */
    async setBacklight(on = true) {
        const mode = on ? "ON" : "OFF";
        return await this.sendCommand(`LCD:BACKLIGHT:${mode}`);
    }

    /**
     * 특정 위치에 텍스트 출력
     * @param {number} row - 행 (0-base)
     * @param {number} col - 열 (0-base)
     * @param {string} text - 출력할 텍스트
     * @returns {Promise<boolean>}
     */
    async print(row, col, text) {
        if (typeof row !== 'number' || typeof col !== 'number') {
            throw new Error("row, col 은 숫자여야 합니다.");
        }
        if (text == null) {
            text = "";
        }

        const safeRow = Math.max(0, row);
        const safeCol = Math.max(0, col);
        const cmd = `LCD:PRINT:${safeRow},${safeCol}:${text}`;
        return await this.sendCommand(cmd);
    }

    /**
     * 0번째 줄 전체 메시지 출력 (헬퍼)
     * @param {string} text
     */
    async printLine1(text) {
        return await this.print(0, 0, text);
    }

    /**
     * 1번째 줄 전체 메시지 출력 (헬퍼, 2행 이상일 때)
     * @param {string} text
     */
    async printLine2(text) {
        return await this.print(1, 0, text);
    }

    _processData(data) {
        // 현재는 LCD 알림 데이터를 특별히 파싱하지 않고 로그만 남깁니다.
        if (!data) return;
        try {
            let dataStr;
            if (data && typeof data === 'object' && data.data !== undefined) {
                const actual = data.data;
                if (actual instanceof ArrayBuffer) {
                    const decoder = new TextDecoder('utf-8');
                    dataStr = decoder.decode(new DataView(actual));
                } else if (actual instanceof DataView) {
                    const decoder = new TextDecoder('utf-8');
                    dataStr = decoder.decode(actual);
                } else if (actual && actual.buffer instanceof ArrayBuffer) {
                    const decoder = new TextDecoder('utf-8');
                    dataStr = decoder.decode(actual);
                } else {
                    dataStr = String(actual);
                }
            } else {
                dataStr = String(data);
            }
            console.log("[LcdDisplay] LCD 알림 수신:", dataStr);
        } catch (e) {
            console.error("[LcdDisplay] 데이터 처리 오류:", e);
        }
    }
}

/**
 * DIY-A 센서 값 가져오기 함수
 * @param {DiyASensor} sensor - DIY-A 센서 인스턴스
 * @param {number} maxRetries - 최대 재시도 횟수
 * @param {number} retryDelay - 재시도 지연 시간 (ms)
 * @returns {Promise<Object|null>} - {raw, voltage} 형태의 객체 또는 null
 */
function getDiyASensorValue(sensor, maxRetries = 3, retryDelay = 100) {
    return new Promise((resolve, reject) => {
        if (!sensor) {
            reject(new Error("유효한 DiyASensor 인스턴스가 필요합니다."));
            return;
        }

        let retries = 0;

        function attempt() {
            const raw = sensor.getRaw();
            const voltage = sensor.getVoltage();

            const hasData = (raw != null || voltage != null);

            if (hasData) {
                resolve({
                    raw,
                    voltage,
                });
            } else if (retries < maxRetries) {
                retries++;
                console.log(`DIY-A 값이 아직 없습니다. 재시도 ${retries}/${maxRetries}`);
                sensor.getStatus().then(() => {
                    setTimeout(attempt, retryDelay);
                }).catch(error => {
                    reject(error);
                });
            } else {
                reject(new Error('DIY-A 센서 데이터를 가져올 수 없습니다.'));
            }
        }

        // 최초 시도
        sensor.getStatus().then(() => {
            setTimeout(attempt, retryDelay);
        }).catch(error => {
            reject(error);
        });
    });
}

/**
 * DIY-A 센서 유효값 가져오기 (Promise 기반)
 * @param {DiyASensor} sensor
 * @returns {Promise<Object>} - {raw, voltage}
 */
async function getValidDiyAValue(sensor) {
    if (!sensor) {
        throw new Error("유효한 DiyASensor 인스턴스가 필요합니다.");
    }
    return await getDiyASensorValue(sensor);
}

/**
 * DIY-B 센서 값 가져오기 함수
 * @param {DiyBSensor} sensor - DIY-B 센서 인스턴스
 * @param {number} maxRetries - 최대 재시도 횟수
 * @param {number} retryDelay - 재시도 지연 시간 (ms)
 * @returns {Promise<Object|null>} - {raw, voltage} 형태의 객체 또는 null
 */
function getDiyBSensorValue(sensor, maxRetries = 3, retryDelay = 100) {
    return new Promise((resolve, reject) => {
        if (!sensor) {
            reject(new Error("유효한 DiyBSensor 인스턴스가 필요합니다."));
            return;
        }

        let retries = 0;

        function attempt() {
            const raw = sensor.getRaw();
            const voltage = sensor.getVoltage();

            const hasData = (raw != null || voltage != null);

            if (hasData) {
                resolve({
                    raw,
                    voltage,
                });
            } else if (retries < maxRetries) {
                retries++;
                console.log(`DIY-B 값이 아직 없습니다. 재시도 ${retries}/${maxRetries}`);
                sensor.getStatus().then(() => {
                    setTimeout(attempt, retryDelay);
                }).catch(error => {
                    reject(error);
                });
            } else {
                reject(new Error('DIY-B 센서 데이터를 가져올 수 없습니다.'));
            }
        }

        // 최초 시도
        sensor.getStatus().then(() => {
            setTimeout(attempt, retryDelay);
        }).catch(error => {
            reject(error);
        });
    });
}

/**
 * DIY-B 센서 유효값 가져오기 (Promise 기반)
 * @param {DiyBSensor} sensor
 * @returns {Promise<Object>} - {raw, voltage}
 */
async function getValidDiyBValue(sensor) {
    if (!sensor) {
        throw new Error("유효한 DiyBSensor 인스턴스가 필요합니다.");
    }
    return await getDiyBSensorValue(sensor);
}

/**
 * Hall 센서 값 가져오기 함수
 * @param {HallSensor} sensor - Hall 센서 인스턴스
 * @param {number} maxRetries - 최대 재시도 횟수
 * @param {number} retryDelay - 재시도 지연 시간 (ms)
 * @returns {Promise<Object|null>} - {raw, strength, density} 형태의 객체 또는 null
 */
function getHallSensorValue(sensor, maxRetries = 3, retryDelay = 100) {
    return new Promise((resolve, reject) => {
        if (!sensor) {
            reject(new Error("유효한 HallSensor 인스턴스가 필요합니다."));
            return;
        }

        let retries = 0;

        function attempt() {
            const raw = sensor.getRaw();
            const strength = sensor.getStrength();
            const density = sensor.getDensity();

            const hasData = (raw != null || strength != null || density != null);

            if (hasData) {
                resolve({
                    raw,
                    strength,
                    density,
                });
            } else if (retries < maxRetries) {
                retries++;
                console.log(`Hall 값이 아직 없습니다. 재시도 ${retries}/${maxRetries}`);
                sensor.getStatus().then(() => {
                    setTimeout(attempt, retryDelay);
                }).catch(error => {
                    reject(error);
                });
            } else {
                reject(new Error('Hall 센서 데이터를 가져올 수 없습니다.'));
            }
        }

        // 최초 시도
        sensor.getStatus().then(() => {
            setTimeout(attempt, retryDelay);
        }).catch(error => {
            reject(error);
        });
    });
}

/**
 * Hall 센서 유효값 가져오기 (Promise 기반)
 * @param {HallSensor} sensor
 * @returns {Promise<Object>} - {raw, strength, density}
 */
async function getValidHallValue(sensor) {
    if (!sensor) {
        throw new Error("유효한 HallSensor 인스턴스가 필요합니다.");
    }
    return await getHallSensorValue(sensor);
}

/**
 * EZLIGHT 센서 값 가져오기 함수
 * @param {EzLightSensor} sensor - EZLIGHT 센서 인스턴스
 * @param {number} maxRetries - 최대 재시도 횟수
 * @param {number} retryDelay - 재시도 지연 시간 (ms)
 * @returns {Promise<Object|null>} - {raw, percent} 형태의 객체 또는 null
 */
function getEzLightSensorValue(sensor, maxRetries = 3, retryDelay = 100) {
    return new Promise((resolve, reject) => {
        if (!sensor) {
            reject(new Error("유효한 EzLightSensor 인스턴스가 필요합니다."));
            return;
        }

        let retries = 0;

        function attempt() {
            const raw = sensor.getRaw();
            const percent = sensor.getPercent();

            const hasData = (raw != null || percent != null);

            if (hasData) {
                resolve({
                    raw,
                    percent,
                });
            } else if (retries < maxRetries) {
                retries++;
                console.log(`EZLIGHT 값이 아직 없습니다. 재시도 ${retries}/${maxRetries}`);
                sensor.getStatus().then(() => {
                    setTimeout(attempt, retryDelay);
                }).catch(error => {
                    reject(error);
                });
            } else {
                reject(new Error('EZLIGHT 센서 데이터를 가져올 수 없습니다.'));
            }
        }

        // 최초 시도
        sensor.getStatus().then(() => {
            setTimeout(attempt, retryDelay);
        }).catch(error => {
            reject(error);
        });
    });
}

/**
 * EZLIGHT 센서 유효값 가져오기 (Promise 기반)
 * @param {EzLightSensor} sensor
 * @returns {Promise<Object>} - {raw, percent}
 */
async function getValidEzLightValue(sensor) {
    if (!sensor) {
        throw new Error("유효한 EzLightSensor 인스턴스가 필요합니다.");
    }
    return await getEzLightSensorValue(sensor);
}

/**
 * EZVOLT 센서 값 가져오기 함수
 * @param {EzVoltSensor} sensor - EZVOLT 센서 인스턴스
 * @param {number} maxRetries - 최대 재시도 횟수
 * @param {number} retryDelay - 재시도 지연 시간 (ms)
 * @returns {Promise<Object|null>} - {raw, voltage} 형태의 객체 또는 null
 */
function getEzVoltSensorValue(sensor, maxRetries = 3, retryDelay = 100) {
    return new Promise((resolve, reject) => {
        if (!sensor) {
            reject(new Error("유효한 EzVoltSensor 인스턴스가 필요합니다."));
            return;
        }

        let retries = 0;

        function attempt() {
            const raw = sensor.getRaw();
            const voltage = sensor.getVoltage();

            const hasData = (raw != null || voltage != null);

            if (hasData) {
                resolve({
                    raw,
                    voltage,
                });
            } else if (retries < maxRetries) {
                retries++;
                console.log(`EZVOLT 값이 아직 없습니다. 재시도 ${retries}/${maxRetries}`);
                sensor.getStatus().then(() => {
                    setTimeout(attempt, retryDelay);
                }).catch(error => {
                    reject(error);
                });
            } else {
                reject(new Error('EZVOLT 센서 데이터를 가져올 수 없습니다.'));
            }
        }

        // 최초 시도
        sensor.getStatus().then(() => {
            setTimeout(attempt, retryDelay);
        }).catch(error => {
            reject(error);
        });
    });
}

/**
 * EZVOLT 센서 유효값 가져오기 (Promise 기반)
 * @param {EzVoltSensor} sensor
 * @returns {Promise<Object>} - {raw, voltage}
 */
async function getValidEzVoltValue(sensor) {
    if (!sensor) {
        throw new Error("유효한 EzVoltSensor 인스턴스가 필요합니다.");
    }
    return await getEzVoltSensorValue(sensor);
}

/**
 * EZTHERMAL 센서 값 가져오기 함수
 * @param {EzThermalSensor} sensor - EZTHERMAL 센서 인스턴스
 * @param {number} maxRetries - 최대 재시도 횟수
 * @param {number} retryDelay - 재시도 지연 시간 (ms)
 * @returns {Promise<Object|null>} - {temperature} 형태의 객체 또는 null
 */
function getEzThermalSensorValue(sensor, maxRetries = 3, retryDelay = 100) {
    return new Promise((resolve, reject) => {
        if (!sensor) {
            reject(new Error("유효한 EzThermalSensor 인스턴스가 필요합니다."));
            return;
        }

        let retries = 0;

        function attempt() {
            const temperature = sensor.getTemperature();

            const hasData = (temperature !== null && temperature !== undefined);

            if (hasData) {
                resolve({ temperature });
            } else if (retries < maxRetries) {
                retries++;
                console.log(`EZTHERMAL 값이 아직 없습니다. 재시도 ${retries}/${maxRetries}`);
                sensor.getStatus().then(() => {
                    setTimeout(attempt, retryDelay);
                }).catch(error => {
                    reject(error);
                });
            } else {
                reject(new Error('EZTHERMAL 센서 데이터를 가져올 수 없습니다.'));
            }
        }

        sensor.getStatus().then(() => {
            setTimeout(attempt, retryDelay);
        }).catch(error => {
            reject(error);
        });
    });
}

/**
 * EZTHERMAL 센서 유효값 가져오기 (Promise 기반)
 * @param {EzThermalSensor} sensor
 * @returns {Promise<Object>} - {temperature}
 */
async function getValidEzThermalValue(sensor) {
    if (!sensor) {
        throw new Error("유효한 EzThermalSensor 인스턴스가 필요합니다.");
    }
    const result = await getEzThermalSensorValue(sensor);
    const t = result && result.temperature;
    if (t === null || t === undefined) {
        throw new Error("유효한 EZTHERMAL 센서 값이 없습니다.");
    }
    return result;
}

/**
 * EZSOUND 센서 값 가져오기 함수
 * @param {EzSoundSensor} sensor - EZSOUND 센서 인스턴스
 * @param {number} maxRetries - 최대 재시도 횟수
 * @param {number} retryDelay - 재시도 지연 시간 (ms)
 * @returns {Promise<Object|null>} - {raw, percent} 형태의 객체 또는 null
 */
function getEzSoundSensorValue(sensor, maxRetries = 3, retryDelay = 100) {
    return new Promise((resolve, reject) => {
        if (!sensor) {
            reject(new Error("유효한 EzSoundSensor 인스턴스가 필요합니다."));
            return;
        }

        let retries = 0;

        function attempt() {
            const raw = sensor.getRaw();
            const percent = sensor.getPercent();

            const hasData = (raw != null || percent != null);

            if (hasData) {
                resolve({
                    raw,
                    percent,
                });
            } else if (retries < maxRetries) {
                retries++;
                console.log(`EZSOUND 값이 아직 없습니다. 재시도 ${retries}/${maxRetries}`);
                sensor.getStatus().then(() => {
                    setTimeout(attempt, retryDelay);
                }).catch(error => {
                    reject(error);
                });
            } else {
                reject(new Error('EZSOUND 센서 데이터를 가져올 수 없습니다.'));
            }
        }

        // 최초 시도
        sensor.getStatus().then(() => {
            setTimeout(attempt, retryDelay);
        }).catch(error => {
            reject(error);
        });
    });
}

/**
 * EZSOUND 센서 유효값 가져오기 (Promise 기반)
 * @param {EzSoundSensor} sensor
 * @returns {Promise<Object>} - {raw, percent}
 */
async function getValidEzSoundValue(sensor) {
    if (!sensor) {
        throw new Error("유효한 EzSoundSensor 인스턴스가 필요합니다.");
    }
    return await getEzSoundSensorValue(sensor);
}

/**
 * EZWEIGHT 센서 값 가져오기 함수
 * @param {EzWeightSensor} sensor - EZWEIGHT 센서 인스턴스
 * @param {number} maxRetries - 최대 재시도 횟수
 * @param {number} retryDelay - 재시도 지연 시간 (ms)
 * @returns {Promise<Object|null>} - {raw, weight} 형태의 객체 또는 null
 */
function getEzWeightSensorValue(sensor, maxRetries = 3, retryDelay = 150) {
    return new Promise((resolve, reject) => {
        if (!sensor) {
            reject(new Error("유효한 EzWeightSensor 인스턴스가 필요합니다."));
            return;
        }

        let retries = 0;

        function attempt() {
            const raw = sensor.getRaw();
            const weight = sensor.getWeight();

            const hasData = (raw != null || weight != null);

            if (hasData) {
                resolve({
                    raw,
                    weight,
                });
            } else if (retries < maxRetries) {
                retries++;
                console.log(`EZWEIGHT 값이 아직 없습니다. 재시도 ${retries}/${maxRetries}`);
                sensor.getStatus().then(() => {
                    setTimeout(attempt, retryDelay);
                }).catch(error => {
                    reject(error);
                });
            } else {
                reject(new Error('EZWEIGHT 센서 데이터를 가져올 수 없습니다.'));
            }
        }

        // 최초 시도
        sensor.getStatus().then(() => {
            setTimeout(attempt, retryDelay);
        }).catch(error => {
            reject(error);
        });
    });
}

/**
 * EZWEIGHT 센서 유효값 가져오기 (Promise 기반)
 * @param {EzWeightSensor} sensor
 * @returns {Promise<Object>} - {raw, weight}
 */
async function getValidEzWeightValue(sensor) {
    if (!sensor) {
        throw new Error("유효한 EzWeightSensor 인스턴스가 필요합니다.");
    }
    return await getEzWeightSensorValue(sensor);
}

/**
 * EZDUST 센서 값 가져오기 함수
 * @param {EzDustSensor} sensor - EZDUST 센서 인스턴스
 * @param {number} maxRetries - 최대 재시도 횟수
 * @param {number} retryDelay - 재시도 지연 시간 (ms)
 * @returns {Promise<Object|null>} - {pm10, pm2_5, pm1_0} 형태의 객체 또는 null
 */
function getEzDustSensorValue(sensor, maxRetries = 3, retryDelay = 150) {
    return new Promise((resolve, reject) => {
        if (!sensor) {
            reject(new Error("유효한 EzDustSensor 인스턴스가 필요합니다."));
            return;
        }

        let retries = 0;

        function attempt() {
            const pm10  = sensor.getPm10();
            const pm2_5 = sensor.getPm2_5();
            const pm1_0 = sensor.getPm1_0();

            const hasData = (pm10 != null || pm2_5 != null || pm1_0 != null);

            if (hasData) {
                resolve({
                    pm10,
                    pm2_5,
                    pm1_0,
                });
            } else if (retries < maxRetries) {
                retries++;
                console.log(`EZDUST 값이 아직 없습니다. 재시도 ${retries}/${maxRetries}`);
                sensor.getStatus().then(() => {
                    setTimeout(attempt, retryDelay);
                }).catch(error => {
                    reject(error);
                });
            } else {
                reject(new Error('EZDUST 센서 데이터를 가져올 수 없습니다.'));
            }
        }

        // 최초 시도
        sensor.getStatus().then(() => {
            setTimeout(attempt, retryDelay);
        }).catch(error => {
            reject(error);
        });
    });
}

/**
 * EZDUST 센서 유효값 가져오기 (Promise 기반)
 * @param {EzDustSensor} sensor
 * @returns {Promise<Object>} - {pm10, pm2_5, pm1_0}
 */
async function getValidEzDustValue(sensor) {
    if (!sensor) {
        throw new Error("유효한 EzDustSensor 인스턴스가 필요합니다.");
    }
    return await getEzDustSensorValue(sensor);
}

/**
 * EZCURR 센서 값 가져오기 함수
 * @param {EzCurrSensor} sensor - EZCURR 센서 인스턴스
 * @param {number} maxRetries - 최대 재시도 횟수
 * @param {number} retryDelay - 재시도 지연 시간 (ms)
 * @returns {Promise<Object|null>} - {current_mA, voltage} 형태의 객체 또는 null
 */
function getEzCurrSensorValue(sensor, maxRetries = 3, retryDelay = 100) {
    return new Promise((resolve, reject) => {
        if (!sensor) {
            reject(new Error("유효한 EzCurrSensor 인스턴스가 필요합니다."));
            return;
        }

        let retries = 0;

        function attempt() {
            const current_mA = sensor.getCurrent();
            const voltage = sensor.getVoltage();

            const hasData = (current_mA != null || voltage != null);

            if (hasData) {
                resolve({
                    current_mA,
                    voltage,
                });
            } else if (retries < maxRetries) {
                retries++;
                console.log(`EZCURR 값이 아직 없습니다. 재시도 ${retries}/${maxRetries}`);
                sensor.getStatus().then(() => {
                    setTimeout(attempt, retryDelay);
                }).catch(error => {
                    reject(error);
                });
            } else {
                reject(new Error('EZCURR 센서 데이터를 가져올 수 없습니다.'));
            }
        }

        // 최초 시도
        sensor.getStatus().then(() => {
            setTimeout(attempt, retryDelay);
        }).catch(error => {
            reject(error);
        });
    });
}

/**
 * EZCURR 센서 유효값 가져오기 (Promise 기반)
 * @param {EzCurrSensor} sensor
 * @returns {Promise<Object>} - {current_mA, voltage}
 */
async function getValidEzCurrValue(sensor) {
    if (!sensor) {
        throw new Error("유효한 EzCurrSensor 인스턴스가 필요합니다.");
    }
    return await getEzCurrSensorValue(sensor);
}

/**
 * EZMaker 기압센서 클래스 (BMP280, EZPRESS)
 * SensorBase 상속, EZ_PRESS_CHARACTERISTIC 사용
 */
class EzPressSensor extends SensorBase {
    constructor() {
        super('EzPress', EZ_PRESS_CHARACTERISTIC);
        this.temperature = null; // 온도 (℃)
        this.pressure = null;    // 기압 (hPa)
    }

    getTemperature() {
        return this.temperature;
    }

    getPressure() {
        return this.pressure;
    }

    async getStatus() {
        console.log("EZ기압센서 상태 요청 전송");
        return await this.sendCommand("EZPRESS:STATUS");
    }

    async setPin(sdaPin, sclPin) {
        return await this.sendCommand(`EZPRESS:PIN:${sdaPin},${sclPin}`);
    }

    _processData(data) {
        if (!data) return;

        console.log("[EzPressSensor] 데이터 수신 확인:", data);

        let actualData = data;
        if (data && typeof data === 'object' && data.data !== undefined) {
            console.log("[EzPressSensor] data.data 구조 감지, 내부 데이터 사용");
            actualData = data.data;
        }

        let dataStr;
        try {
            if (actualData instanceof ArrayBuffer) {
                const decoder = new TextDecoder('utf-8');
                dataStr = decoder.decode(new DataView(actualData));
            } else if (actualData instanceof DataView) {
                const decoder = new TextDecoder('utf-8');
                dataStr = decoder.decode(actualData);
            } else if (actualData && actualData.buffer instanceof ArrayBuffer) {
                const decoder = new TextDecoder('utf-8');
                dataStr = decoder.decode(actualData);
            } else {
                dataStr = String(actualData);
            }
        } catch (e) {
            console.error("[EzPressSensor] 데이터 변환 오류:", e);
            dataStr = String(actualData || "");
        }

        try {
            // EZPRESS:T=...,P=...
            if (dataStr.startsWith("EZPRESS:")) {
                const body = dataStr.substring(8); // "EZPRESS:" 제거
                const parts = body.split(',');
                for (const part of parts) {
                    if (!part.includes('=')) continue;
                    const [key, val] = part.split('=');
                    const f = parseFloat(val);
                    switch (key) {
                        case 'T': this.temperature = f; break;
                        case 'P': this.pressure = f; break;
                    }
                }
                console.log(`[EzPressSensor] 파싱 결과: T=${this.temperature}, P=${this.pressure}`);
            }
        } catch (e) {
            console.error("[EzPressSensor] 데이터 파싱 오류:", e);
        }
    }
}

/**
 * EZ기압센서 값 가져오기 함수
 * @param {EzPressSensor} sensor - EZ기압센서 인스턴스
 * @param {number} maxRetries - 최대 재시도 횟수
 * @param {number} retryDelay - 재시도 지연 시간 (ms)
 * @returns {Promise<Object|null>} - {temperature, pressure} 형태의 객체 또는 null
 */
function getEzPressSensorValue(sensor, maxRetries = 3, retryDelay = 100) {
    return new Promise((resolve, reject) => {
        let retries = 0;

        function attempt() {
            const temperature = sensor.getTemperature();
            const pressure    = sensor.getPressure();

            const hasData = (temperature != null || pressure != null);

            if (hasData) {
                resolve({
                    temperature,
                    pressure,
                });
            } else if (retries < maxRetries) {
                retries++;
                console.log(`EZPress 값이 아직 없습니다. 재시도 ${retries}/${maxRetries}`);
                sensor.getStatus().then(() => {
                    setTimeout(attempt, retryDelay);
                }).catch(error => {
                    reject(error);
                });
            } else {
                reject(new Error('EZ기압센서 데이터를 가져올 수 없습니다.'));
            }
        }

        // 최초 시도
        sensor.getStatus().then(() => {
            setTimeout(attempt, retryDelay);
        }).catch(error => {
            reject(error);
        });
    });
}

/**
 * EZ기압센서 유효값 가져오기 (Promise 기반)
 * @param {EzPressSensor} sensor
 * @returns {Promise<Object>} - {temperature, pressure}
 */
async function getValidEzPressValue(sensor) {
    if (!sensor) {
        throw new Error("유효한 EzPressSensor 인스턴스가 필요합니다.");
    }
    return await getEzPressSensorValue(sensor);
}

class HeartRateSensor extends SensorBase {
    constructor() {
        super('HeartRate', HEART_CHARACTERISTIC);
        this._bpm = null;  // 가장 최근 측정된 심박수 값
        this._isStreaming = false;
    }

    /**
     * 현재 저장된 BPM 값 반환
     * @return {Number|null} 심박수 또는 null
     */
    getBPM() {
        return this._bpm;
    }

    /**
     * 심박수 상태 요청 
     */
    async getStatus() {
        return await this.sendCommand('HEART:STATUS');
        // 응답은 _processData에서 자동으로 처리되어 this._bpm에 저장됨
    }

    /**
     * 핀 설정
     */
    async setPin(sdaPin, sclPin) {
        await this.sendCommand(`HEART:PIN:${sdaPin},${sclPin}`);
        return true;
    }

    /**
     * 스트리밍 모드 시작 - 자동으로 값을 업데이트
     */
    async startStreaming() {
        this._isStreaming = true;
        return await this.sendCommand('HEART:STREAM:ON');
    }

    /**
     * 스트리밍 모드 중지
     */
    async stopStreaming() {
        this._isStreaming = false;
        return await this.sendCommand('HEART:STREAM:OFF');
    }

    /**
     * 스트리밍 활성화 상태 확인
     */
    isStreaming() {
        return this._isStreaming;
    }

    /**
     * 데이터 처리 - 내부 값만 업데이트
     * @private
     */
    _processData(data) {
        try {
            // 데이터 형식에 따른 처리
            let dataStr;

            if (data instanceof DataView || data instanceof ArrayBuffer) {
                // 바이너리 데이터 처리 (필요한 경우)
                const decoder = new TextDecoder('utf-8');
                dataStr = decoder.decode(data instanceof DataView ? data : new DataView(data));
            } else if (data && typeof data === 'object' && data.data) {
                // data.data 구조 처리
                const decoder = new TextDecoder('utf-8');
                if (data.data instanceof ArrayBuffer) {
                    dataStr = decoder.decode(new DataView(data.data));
                } else if (data.data instanceof DataView) {
                    dataStr = decoder.decode(data.data);
                } else if (data.data.buffer instanceof ArrayBuffer) {
                    dataStr = decoder.decode(data.data);
                } else {
                    dataStr = String(data.data);
                }
            } else {
                // 기타 형식 처리
                dataStr = String(data || "");
            }

            // 문자열에서 심박수 값 추출
            if (dataStr.startsWith('HEART:')) {
                const bpmStr = dataStr.substring('HEART:'.length);
                const bpm = parseInt(bpmStr, 10);

                if (!isNaN(bpm)) {
                    // 값의 범위 확인 (30-200 BPM 정도가 정상적인 인간 심박수 범위)
                    if (bpm >= 30 && bpm <= 200) {
                        this._bpm = bpm;
                        console.log(`[HeartRateSensor] 심박수 업데이트: ${this._bpm} BPM`);
                    } else {
                        console.warn(`[HeartRateSensor] 비정상 심박수 값 무시: ${bpm}`);
                    }
                }
            }
        } catch (error) {
            console.error('Error processing heart rate data:', error);
        }
    }
}

/**
 * Get heart rate value with retries
 * @param {HeartRateSensor} sensor - Heart rate sensor instance
 * @param {Number} maxRetries - Maximum number of retry attempts
 * @param {Number} retryDelay - Delay between retries in ms
 * @return {Promise<Number>} Heart rate in BPM
 */
function getHeartRateValue(sensor, maxRetries = 3, retryDelay = 50) {
    return new Promise((resolve, reject) => {
        // 스트리밍 상태 확인
        if (!sensor.isStreaming()) {
            // 스트리밍이 아니라면 경고 로그
            console.warn("Heart rate sensor not streaming. Stored value may be outdated.");
            // 여기서 getStatus() 호출은 하지 않음
        }

        let retries = 0;

        function attempt() {
            const bpm = sensor.getBPM();
            if (bpm !== null) {
                resolve(bpm);
            } else if (retries < maxRetries) {
                retries++;
                setTimeout(attempt, retryDelay);
            } else {
                // 심박 측정이 어려울 때 사용자 친화적인 오류 메시지
                reject(new Error('심박 데이터를 가져올 수 없습니다. 센서 위치를 확인하거나 스트리밍을 시작하세요.'));
            }
        }

        attempt();
    });
}

/**
 * Get valid heart rate value
 * @param {HeartRateSensor} sensor - Heart rate sensor instance
 * @return {Promise<Number>} Heart rate in BPM
 */
async function getValidHeartRateValue(sensor) {
    try {
        const bpm = await getHeartRateValue(sensor);
        return bpm;
    } catch (error) {
        console.error('Error getting valid heart rate value:', error);
        throw error;
    }
}

/**
 * 인체감지 센서 값 가져오기 함수
 * @param {HumanSensor} sensor - 인체감지 센서 인스턴스
 * @param {number} maxRetries - 최대 재시도 횟수
 * @param {number} retryDelay - 재시도 지연 시간 (ms)
 * @returns {Promise<number|null>} - 0 또는 1, 실패 시 null
 */
function getHumanSensorValue(sensor, maxRetries = 3, retryDelay = 100) {
    return new Promise((resolve, reject) => {
        if (!sensor) {
            reject(new Error("유효한 HumanSensor 인스턴스가 필요합니다."));
            return;
        }

        let retries = 0;

        function attempt() {
            const value = sensor.getValue();

            const hasData = (value !== null && value !== undefined);

            if (hasData) {
                resolve(value);
            } else if (retries < maxRetries) {
                retries++;
                console.log(`HUMAN 값이 아직 없습니다. 재시도 ${retries}/${maxRetries}`);
                sensor.getStatus().then(() => {
                    setTimeout(attempt, retryDelay);
                }).catch(error => {
                    reject(error);
                });
            } else {
                reject(new Error('HUMAN 센서 데이터를 가져올 수 없습니다.'));
            }
        }

        sensor.getStatus().then(() => {
            setTimeout(attempt, retryDelay);
        }).catch(error => {
            reject(error);
        });
    });
}

/**
 * 인체감지 센서 유효값 가져오기 (Promise 기반)
 * @param {HumanSensor} sensor
 * @returns {Promise<number>} - 0 또는 1
 */
async function getValidHumanValue(sensor) {
    if (!sensor) {
        throw new Error("유효한 HumanSensor 인스턴스가 필요합니다.");
    }
    const v = await getHumanSensorValue(sensor);
    if (v === null || v === undefined) {
        throw new Error("유효한 HUMAN 센서 값이 없습니다.");
    }
    return v;
}

// 전역 객체에 추가
window.BLECommandQueue = BLECommandQueue;
window.BLECore = BLECore;
window.BLEManager = BLEManager;
window.LED = LED;
window.Laser = Laser;
window.Camera = Camera;
window.LightSensor = LightSensor;
window.UltrasonicSensor = UltrasonicSensor;
window.DHTSensor = DHTSensor;
window.TouchSensor = TouchSensor;
window.DustSensor = DustSensor;
window.GyroSensor = GyroSensor;      // GyroSensor 클래스 추가
window.EzGyroSensor = EzGyroSensor;  // EzGyroSensor 클래스 추가
window.EzPressSensor = EzPressSensor; // EzPressSensor 클래스 추가
window.EzCo2Sensor = EzCo2Sensor;   // EzCo2Sensor 클래스 추가
window.ServoMotor = ServoMotor;
window.DCMotor = DCMotor;  // DCMotor 클래스 추가
window.NeoPixel = NeoPixel;  // NeoPixel 클래스 추가
window.Buzzer = Buzzer;  // Buzzer 클래스 추가
window.HeartRateSensor = HeartRateSensor;  // HeartRateSensor 클래스 추가
window.LcdDisplay = LcdDisplay;  // I2C LCD 디스플레이 클래스 추가
window.EzLightSensor = EzLightSensor; // EZMaker 밝기센서(EZLIGHT) 클래스 추가
window.EzVoltSensor = EzVoltSensor;   // EZMaker 전압센서(EZVOLT) 클래스 추가
window.EzCurrSensor = EzCurrSensor;   // EZMaker 전류센서(EZCURR) 클래스 추가
window.EzThermalSensor = EzThermalSensor; // EZMaker 수중/접촉 온도센서(EZTHERMAL) 클래스 추가
window.EzSoundSensor = EzSoundSensor; // EZMaker 소리센서(EZSOUND) 클래스 추가
window.EzWeightSensor = EzWeightSensor; // EZMaker 무게센서(EZWEIGHT, HX711) 클래스 추가
window.EzDustSensor = EzDustSensor;     // EZMaker 미세먼지 센서(EZDUST, PMS7003M) 클래스 추가

// 전역 함수 추가
window.blinkLED = blinkLED;
window.stopBlinking = stopBlinking;

window.getLightSensorValue = getLightSensorValue;
window.getUltrasonicSensorValue = getUltrasonicSensorValue;
window.getDHTSensorValue = getDHTSensorValue;
window.getDustSensorValue = getDustSensorValue;  // 먼지 센서 함수 추가
window.getGyroSensorValue = getGyroSensorValue; // 자이로센서 함수 추가
window.getHeartRateValue = getHeartRateValue; // 심장박동 센서 함수 추가
window.getEzPressSensorValue = getEzPressSensorValue; // EZ기압센서 함수 추가
window.getEzCo2SensorValue = getEzCo2SensorValue; // EZCO2 센서 함수 추가
window.getEzLightSensorValue = getEzLightSensorValue;   // EZLIGHT 센서 함수 추가
window.getEzVoltSensorValue = getEzVoltSensorValue;     // EZVOLT 센서 함수 추가
window.getEzThermalSensorValue = getEzThermalSensorValue; // EZTHERMAL 센서 함수 추가
window.getEzSoundSensorValue = getEzSoundSensorValue;     // EZSOUND 센서 함수 추가

window.getValidLightSensorValue = getValidLightSensorValue;
window.getValidUltrasonicValue = getValidUltrasonicValue;
window.getValidDHTValue = getValidDHTValue;
window.getValidDustValue = getValidDustValue;  // 먼지 센서 유효값 함수 추가
window.getValidGyroValue = getValidGyroValue; // 자이로센서 유효값 함수 추가
window.getValidHeartRateValue = getValidHeartRateValue; // 심장박동 센서 유효값 함수 추가
window.getValidEzPressValue = getValidEzPressValue; // EZ기압센서 유효값 함수 추가
window.getValidEzCo2Value = getValidEzCo2Value; // EZCO2 센서 유효값 함수 추가
window.getEzGyroSensorValue = getEzGyroSensorValue; // EZ자이로센서 함수 추가
window.getValidEzGyroValue = getValidEzGyroValue;   // EZ자이로센서 유효값 함수 추가
window.ensureEzGyroCache = ensureEzGyroCache;       // EZ자이로 캐시 헬퍼 추가
window.clearEzGyroCache = clearEzGyroCache;         // EZ자이로 캐시 초기화 헬퍼 추가
window.getValidEzLightValue = getValidEzLightValue;     // EZLIGHT 센서 유효값 함수 추가
window.getValidEzVoltValue = getValidEzVoltValue;       // EZVOLT 센서 유효값 함수 추가
window.getEzCurrSensorValue = getEzCurrSensorValue;     // EZCURR 센서 함수 추가
window.getValidEzCurrValue = getValidEzCurrValue;       // EZCURR 센서 유효값 함수 추가
window.getValidEzThermalValue = getValidEzThermalValue; // EZTHERMAL 센서 유효값 함수 추가
window.getValidEzSoundValue = getValidEzSoundValue;     // EZSOUND 센서 유효값 함수 추가
window.getEzWeightSensorValue = getEzWeightSensorValue; // EZWEIGHT 센서 함수 추가
window.getValidEzWeightValue = getValidEzWeightValue;   // EZWEIGHT 센서 유효값 함수 추가
window.getEzDustSensorValue = getEzDustSensorValue;     // EZDUST 센서 함수 추가
window.getValidEzDustValue = getValidEzDustValue;       // EZDUST 센서 유효값 함수 추가




window.bleManager = BLEManager.getInstance();

// 다중 서보모터 사용 예제
// --------------------------------------
// Example: 
// const servo = new ServoMotor();
// // 첫 번째 서보
// await servo.setPin(5);  // 첫 번째 서보 핀 설정
// await servo.setAngle(90);  // 첫 번째 서보 각도 설정
// const angle1 = servo.getAngle();  // 첫 번째 서보 현재 각도 가져오기
// 
// // 두 번째 서보
// await servo.setPin2(6);  // 두 번째 서보 핀 설정
// await servo.setAngle2(45);  // 두 번째 서보 각도 설정
// const angle2 = servo.getAngle2();  // 두 번째 서보 현재 각도 가져오기
// 
// // 인덱스 기반 접근
// await servo.setPinByIndex(1, 5);  // 첫 번째 서보 핀 설정
// await servo.setPinByIndex(2, 6);  // 두 번째 서보 핀 설정
// await servo.setAngleByIndex(1, 90);  // 첫 번째 서보 각도 설정
// await servo.setAngleByIndex(2, 45);  // 두 번째 서보 각도 설정
// const angle1 = servo.getAngleByIndex(1);  // 첫 번째 서보 현재 각도 가져오기
// const angle2 = servo.getAngleByIndex(2);  // 두 번째 서보 현재 각도 가져오기

// SerialManager 클래스 - 시리얼 통신 관리
class SerialManager {
    constructor() {
        this._serialPort = null;
        this._serialReader = null;
        this._readTimeout = null;
        this._ESP32_BAUD_RATE = 115200;
        
        // 콜백 객체
        this._callbacks = {
            onConnect: [],
            onDisconnect: [],
            onData: [],
            onBleNameExtracted: [],
            onError: []
        };
        
        // 상태
        this._isConnected = false;
    }
    
    // 싱글톤 인스턴스 반환
    static getInstance() {
        if (!SerialManager._instance) {
            SerialManager._instance = new SerialManager();
        }
        return SerialManager._instance;
    }
    
    // 연결 상태 확인
    get isConnected() {
        return this._isConnected && this._serialPort && this._serialPort.readable;
    }
    
    // 콜백 등록 함수들
    onConnect(callback) {
        if (typeof callback === 'function') {
            this._callbacks.onConnect.push(callback);
        }
        return this;
    }
    
    onDisconnect(callback) {
        if (typeof callback === 'function') {
            this._callbacks.onDisconnect.push(callback);
        }
        return this;
    }
    
    onData(callback) {
        if (typeof callback === 'function') {
            this._callbacks.onData.push(callback);
        }
        return this;
    }
    
    onBleNameExtracted(callback) {
        if (typeof callback === 'function') {
            this._callbacks.onBleNameExtracted.push(callback);
        }
        return this;
    }
    
    onError(callback) {
        if (typeof callback === 'function') {
            this._callbacks.onError.push(callback);
        }
        return this;
    }
    
    // 콜백 호출 내부 함수
    _triggerCallbacks(type, data) {
        if (this._callbacks[type]) {
            this._callbacks[type].forEach(callback => {
                try {
                    callback(data);
                } catch (error) {
                    console.error(`Error in ${type} callback:`, error);
                }
            });
        }
    }
    
    // BLE 이름 추출 함수
    extractBLEName(text) {
        // "Device name:" 패턴을 찾아 BLE 이름 추출
        const deviceNameMatch = text.match(/Device name:\s+([A-Z0-9]+)/);
        if (deviceNameMatch && deviceNameMatch[1]) {
            const bleName = deviceNameMatch[1].trim();
            
            // DCB로 시작하고 9자리인지 확인 (DCB + 6자리 코드)
            if (bleName.startsWith('DCB') && bleName.length === 9) {
                console.log('BLE 이름 추출됨:', bleName);
                this._triggerCallbacks('onBleNameExtracted', bleName);
                return bleName;
            }
        }
        return null;
    }
    
    // 시리얼 연결 시작
    async connect() {
        // 이미 연결된 경우 처리
        if (this.isConnected) {
            console.log('이미 시리얼 포트에 연결되어 있습니다.');
            return;
        }
        
        try {
            // 시리얼 포트 요청
            this._serialPort = await navigator.serial.requestPort();
            
            // 시리얼 포트 열기
            await this._serialPort.open({ 
                baudRate: this._ESP32_BAUD_RATE,
                dataBits: 8,
                stopBits: 1,
                parity: 'none',
                flowControl: 'none'
            });
            
            // 상태 업데이트
            this._isConnected = true;
            
            // 읽기 스트림 설정
            this._setupSerialReader();
            
            // 읽기 루프 시작
            this._startSerialReading();
            
            // 연결 이벤트 발생
            this._triggerCallbacks('onConnect', { port: this._serialPort });
            
            console.log('ESP32-S3 시리얼 연결 성공');
            
            return true;
        } catch (error) {
            console.error('시리얼 연결 오류:', error);
            this._triggerCallbacks('onError', { error, message: '시리얼 연결 오류' });
            throw error;
        }
    }
    
    // 시리얼 연결 종료
    async disconnect() {
        // 읽기 스트림 정리
        if (this._serialReader) {
            try {
                await this._serialReader.cancel();
                // cancel 후 다시 null 체크
                if (this._serialReader) {
                    await this._serialReader.releaseLock();
                }
            } catch (error) {
                console.error('시리얼 리더 정리 오류:', error);
            }
            this._serialReader = null;
        }
        
        // 시리얼 포트 닫기
        if (this._serialPort) {
            try {
                await this._serialPort.close();
            } catch (error) {
                console.error('시리얼 포트 닫기 오류:', error);
            }
            this._serialPort = null;
        }
        
        // 상태 업데이트
        this._isConnected = false;
        
        // 연결 해제 이벤트 발생
        this._triggerCallbacks('onDisconnect', {});
        
        console.log('시리얼 연결 종료');
    }
    
    // 시리얼 스트림 설정
    async _setupSerialReader() {
        if (!this._serialPort) return;
        
        // 기존 스트림 정리
        if (this._serialReader) {
            try {
                await this._serialReader.cancel();
                // cancel 후 다시 null 체크
                if (this._serialReader) {
                    await this._serialReader.releaseLock();
                }
            } catch (error) {
                console.error('시리얼 리더 정리 오류:', error);
            }
            this._serialReader = null;
        }
        
        // 새 스트림 설정
        if (this._serialPort.readable) {
            this._serialReader = this._serialPort.readable.getReader();
        }
    }
    
    // 시리얼 데이터 읽기 루프
    async _startSerialReading() {
        if (!this._serialReader) return;
        
        // 누적 버퍼 (불완전한 라인을 처리하기 위함)
        let buffer = '';
        
        try {
            while (true) {
                const { value, done } = await this._serialReader.read();
                if (done) {
                    // 읽기 중단
                    break;
                }
                
                // 수신된 데이터 처리 (UTF-8 텍스트로 가정)
                const textDecoder = new TextDecoder();
                const text = textDecoder.decode(value);
                console.log('수신 데이터:', text);
                
                // 줄 단위 처리를 위해 버퍼에 추가
                buffer += text;
                
                // 데이터 수신 이벤트 발생
                this._triggerCallbacks('onData', { text, rawData: value });
                
                // BLE 이름 찾기 위한 추가 검사
                this.extractBLEName(buffer);
                
                // 버퍼 정리 (너무 길어지는 것 방지)
                if (buffer.length > 5000) {
                    buffer = buffer.slice(-2000); // 마지막 2000자만 유지
                }
            }
        } catch (error) {
            console.error('시리얼 데이터 읽기 오류:', error);
            this._triggerCallbacks('onError', { error, message: '시리얼 데이터 읽기 오류' });
        } finally {
            // 읽기 종료시 정리
            if (this._serialReader) {
                try {
                    this._serialReader.releaseLock();
                } catch (error) {
                    console.error('시리얼 리더 락 해제 오류:', error);
                }
                this._serialReader = null;
            }
            
            // 연결 상태 업데이트
            this._isConnected = false;
            
            // 연결 해제 이벤트 발생
            this._triggerCallbacks('onDisconnect', { reason: 'reader_closed' });
        }
    }
}

// 정적 인스턴스 초기화
SerialManager._instance = null;
