/**
 * webFirmwareUploader.js - ESP32-S3 펌웨어 업로드 클래스
 * 
 * === 최신 개선사항 (BLEManager 중앙화된 데이터 수신 구조 활용) ===
 * 1. BLEManager의 onDataReceived 콜백을 통한 중앙화된 ACK 수신
 * 2. 별도의 startNotifications 호출 제거로 충돌 방지
 * 3. integratedBleLib_Camera.js의 완벽한 upgrade 채널 데이터 수신부 활용
 * 4. 향상된 데이터 형식 처리 (ArrayBuffer, DataView, TypedArray, String)
 * 5. 강화된 디버깅 로그로 ACK 수신 문제 추적 가능
 * 
 * 이 방식으로 ACK 수신 문제가 해결되어야 합니다.
 */
class WebFirmwareUploader {
    constructor() {
        // UPGRADE_CHARACTERISTIC 상수 사용 가능 여부 확인
        if (typeof UPGRADE_CHARACTERISTIC === 'undefined') {
            console.error('[WebFirmwareUploader] UPGRADE_CHARACTERISTIC 상수가 정의되지 않았습니다. integratedBleLib_Camera.js가 로드되었는지 확인하세요.');
            throw new Error('UPGRADE_CHARACTERISTIC 상수가 정의되지 않았습니다.');
        }
        
        console.log(`[WebFirmwareUploader] UPGRADE_CHARACTERISTIC 사용: ${UPGRADE_CHARACTERISTIC}`);
        
        this.bleManager = null;  // BLE 매니저로 변경
        this.uploadProgress = 0;
        this.isUploading = false;
        this.firmwareFiles = new Map(); // 업로드할 파일들 저장
        
        // ===== IRQ 최적화 설정 =====
        this.transmissionSettings = {
            // BLE 버퍼 최적화 (서버 512바이트 버퍼 고려)
            maxChunkSize: 450,           // 117바이트에서 87바이트로 축소 (25% 감소)
            transmissionDelay: 150,     // 100ms에서 150ms로 증가 (50% 증가)
            stabilityPause: 500,        // 10청크마다 500ms 안정성 대기
            stabilityInterval: 10,      // 안정성 대기 간격
            
            // 적응형 전송 설정
            adaptiveMode: true,         // 적응형 전송 활성화
            errorThreshold: 3,          // 연속 오류 3회 시 속도 조정
            speedAdjustment: true       // 속도 자동 조정
        };
        
        // 전송 상태 추적
        this.transmissionStats = {
            consecutiveErrors: 0,
            totalChunks: 0,
            successfulChunks: 0,
            retransmissions: 0,
            currentSpeed: 'normal'      // normal, slow, fast
        };
        
        // ===== ACK 기반 확인 통신 설정 =====
        this.ackSettings = {
            timeout: 2000,              // ACK 대기 시간 (2초)
            maxRetries: 7,              // 최대 재전송 횟수
            ackReceived: new Map()      // 수신된 ACK 저장 (chunk_id -> ack_data)
        };
        
        // ACK 핸들러 등록 상태 추적
        this.ackHandlerRegistered = false;
        
        // 콜백 함수들
        this.onProgress = null;
        this.onComplete = null;
        this.onError = null;
        this.onStatus = null;
        
        console.log('[WebFirmwareUploader] 초기화 완료 - IRQ 최적화 모드');
        console.log('[Optimization] 전송 설정:', this.transmissionSettings);
        console.log('[ACK] ACK 기반 확인 통신 활성화');
    }
    
    /**
     * BLE 매니저 설정
     */
    setBleManager(bleManager) {
        console.log('[WebFirmwareUploader] BLE 매니저 설정');
        this.bleManager = bleManager;
        
        // === BLE 연결 해제 시 상태 초기화 ===
        this.bleManager.onDisconnected(() => {
            console.log('[WebFirmwareUploader] BLE 연결 해제 감지 - ACK 핸들러 상태 초기화');
            this.ackHandlerRegistered = false;  // 핸들러 등록 상태 초기화
            this.ackSettings.ackReceived.clear(); // 대기 중인 ACK 데이터 초기화
        });
        
        // BLE 연결 상태에 따른 ACK 핸들러 등록 처리
        if (this.bleManager.isConnected) {
            console.log('[WebFirmwareUploader] BLE가 이미 연결되어 있음 - 즉시 ACK 핸들러 등록');
            this._registerAckHandler();
        } else {
            console.log('[WebFirmwareUploader] BLE가 아직 연결되지 않음 - 연결 완료 후 ACK 핸들러 등록 예약');
            
            // BLE 연결 완료 후 ACK 핸들러 등록
            this.bleManager.onConnected(() => {
                console.log('[WebFirmwareUploader] BLE 연결 완료 - ACK 핸들러 등록');
                // 연결 시에는 항상 재등록 (이전 등록 상태 무시)
                this.ackHandlerRegistered = false; // 강제 초기화
                this._registerAckHandler();
            });
        }
        
        console.log(`[WebFirmwareUploader] sendCommand 타입: ${typeof this.bleManager.sendCommand}`);
    }
    
    /**
     * BLE 매니저 설정 (대문자 표기법 호환성)
     */
    setBLEManager(bleManager) {
        this.setBleManager(bleManager);
    }
    
    /**
     * 진행상황 콜백 설정
     */
    setProgressCallback(callback) {
        this.onProgress = callback;
    }
    
    /**
     * 완료 콜백 설정
     */
    setCompleteCallback(callback) {
        this.onComplete = callback;
    }
    
    /**
     * 오류 콜백 설정
     */
    setErrorCallback(callback) {
        this.onError = callback;
    }
    
    /**
     * 상태 메시지 콜백 설정
     */
    setStatusCallback(callback) {
        this.onStatus = callback;
    }
    
    /**
     * 펌웨어 파일 추가
     */
    addFirmwareFile(filename, fileContent) {
        this.firmwareFiles.set(filename, fileContent);
        console.log(`[WebFirmwareUploader] 파일 추가: ${filename} (${fileContent.length} bytes)`);
    }
    
    /**
     * 파일 업로드 인터페이스에서 펌웨어 패키지 로드
     */
    async loadFirmwarePackage(file) {
        try {
            this._updateStatus('펌웨어 패키지 분석 중...');
            
            if (file.name.endsWith('.zip')) {
                // ZIP 파일 처리
                await this._processZipFile(file);
            } else if (file.name.endsWith('.mpy') || file.name.endsWith('.py')) {
                // 단일 파일 처리
                const content = await this._readFileAsArrayBuffer(file);
                this.addFirmwareFile(file.name, content);
            } else {
                throw new Error('지원하지 않는 파일 형식입니다. (.zip, .mpy, .py 파일만 지원)');
            }
            
            this._updateStatus(`${this.firmwareFiles.size}개 파일 로드 완료`);
            return true;
        } catch (error) {
            this._updateError('펌웨어 패키지 로드 실패: ' + error.message);
            return false;
        }
    }
    
    /**
     * ZIP 파일 처리 (JSZip 라이브러리 필요)
     */
    async _processZipFile(zipFile) {
        // JSZip 라이브러리가 로드되어 있는지 확인
        if (typeof JSZip === 'undefined') {
            throw new Error('JSZip 라이브러리가 필요합니다.');
        }
        
        const zip = new JSZip();
        const zipContent = await this._readFileAsArrayBuffer(zipFile);
        const zipData = await zip.loadAsync(zipContent);
        
        // ZIP 파일 내의 모든 파일 처리
        for (const [filename, fileData] of Object.entries(zipData.files)) {
            if (!fileData.dir && (filename.endsWith('.mpy') || filename.endsWith('.py'))) {
                const content = await fileData.async('arraybuffer');
                this.addFirmwareFile(filename, content);
            }
        }
    }
    
    /**
     * 파일을 ArrayBuffer로 읽기
     */
    _readFileAsArrayBuffer(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = () => resolve(reader.result);
            reader.onerror = () => reject(reader.error);
            reader.readAsArrayBuffer(file);
        });
    }
    
    /**
     * 펌웨어 업로드 시작
     */
    async startUpload() {
        if (this.isUploading) {
            throw new Error('이미 업로드가 진행 중입니다.');
        }
        
        if (this.firmwareFiles.size === 0) {
            throw new Error('업로드할 펌웨어 파일이 없습니다.');
        }
        
        if (!this.bleManager || !this.bleManager.isConnected) {
            throw new Error('BLE 연결이 필요합니다.');
        }
        
        try {
            this.isUploading = true;
            this.uploadProgress = 0;
            
            this._updateStatus('펌웨어 업로드 시작...');
            this._updateProgress(0);
            
            // ACK 핸들러 최종 확인 및 등록 (안전장치)
            if (this.bleManager.isConnected && this.bleManager.server) {
                console.log('[WebFirmwareUploader] BLE 연결 확인됨 - ACK 핸들러 재등록 시도');
                this._registerAckHandler(true);
                
                // 잠시 대기하여 ACK 핸들러가 등록되도록 함
                await this._delay(300);
            } else {
                throw new Error('BLE가 완전히 연결되지 않았습니다. 연결을 확인하고 다시 시도하세요.');
            }
            
            // 1. 보드를 파일 수신 모드로 전환 (REPL 초기화 제거)
            await this._enterFileUploadMode();
            
            // 2. 파일들을 순차적으로 업로드
            const totalFiles = this.firmwareFiles.size;
            let completedFiles = 0;
            
            for (const [filename, content] of this.firmwareFiles) {
                // 파일 경로 결정 (표시용)
                let displayFilename = filename;
                if (filename.endsWith('.mpy') && !filename.startsWith('lib/')) {
                    displayFilename = `lib/${filename}`;
                }
                
                this._updateStatus(`업로드 중: ${displayFilename}`);
                
                await this._uploadSingleFile(filename, content);
                
                completedFiles++;
                const progress = (completedFiles / totalFiles) * 100;
                this._updateProgress(progress);
                
                // 파일 간 짧은 대기
                await this._delay(100);
            }
            
            return; 
            // 3. 업로드 완료 처리
            await this._finishUpload();
            
            this._updateStatus('펌웨어 업로드 완료!');
            this._updateProgress(100);
            
            if (this.onComplete) {
                this.onComplete();
            }
            
        } catch (error) {
            this._updateError('업로드 실패: ' + error.message);
            throw error;
        } finally {
            this.isUploading = false;
        }
    }
    
    /**
     * 보드를 파일 수신 모드로 전환
     */
    async _enterFileUploadMode() {
        // 업그레이드 모드 시작
        await this._sendCommand('UPGRADE:START');
        await this._delay(500);
        
        this._updateStatus('업그레이드 모드 진입 완료');
    }
    
    /**
     * 단일 파일 업로드
     */
    async _uploadSingleFile(filename, content) {
        // === 파일 경로 결정 (.py vs .mpy) ===
        let targetFilename = filename;
        
        // .mpy 파일은 /lib 폴더에 설치해야 함
        if (filename.endsWith('.mpy')) {
            // lib/ 경로가 없으면 추가
            if (!filename.startsWith('lib/')) {
                targetFilename = `lib/${filename}`;
            }
            console.log(`[WebFirmwareUploader] .mpy 파일 - lib 폴더에 설치: ${targetFilename}`);
        } else if (filename.endsWith('.py')) {
            // .py 파일은 루트에 설치 (기본값)
            // lib/으로 시작하는 경우는 그대로 유지
            if (filename.startsWith('lib/')) {
                targetFilename = filename; // lib/somefile.py 그대로 유지
            } else {
                targetFilename = filename; // main.py, boot.py 등은 루트에
            }
            console.log(`[WebFirmwareUploader] .py 파일 - 경로: ${targetFilename}`);
        }
        
        console.log(`[WebFirmwareUploader] 파일 경로 매핑: ${filename} → ${targetFilename}`);
        
        // 1. 파일 전송 시작 알림
        const fileSize = content.byteLength;
        console.log(`[WebFirmwareUploader] 파일 업로드 시작: ${targetFilename} (원본: ${filename}), 크기: ${fileSize}바이트`);
        
        // 파일 형식별 정보 로깅
        if (filename.endsWith('.py')) {
            console.log(`[WebFirmwareUploader] .py 파일 - Python 소스 코드 (텍스트)`);
            // 텍스트 파일의 경우 샘플 내용 확인 (디버깅용)
            try {
                const sampleBytes = new Uint8Array(content.slice(0, Math.min(100, fileSize)));
                const textSample = new TextDecoder('utf-8').decode(sampleBytes);
                console.log(`[WebFirmwareUploader] .py 파일 샘플: ${textSample.substring(0, 50)}...`);
            } catch (error) {
                console.log(`[WebFirmwareUploader] .py 파일 UTF-8 디코딩 실패 (바이너리 포함?)`);
            }
        } else if (filename.endsWith('.mpy')) {
            console.log(`[WebFirmwareUploader] .mpy 파일 - MicroPython 바이트코드 (바이너리)`);
            // 바이너리 파일의 경우 매직 바이트 확인 (디버깅용)
            const magicBytes = new Uint8Array(content.slice(0, Math.min(4, fileSize)));
            console.log(`[WebFirmwareUploader] .mpy 매직 바이트: [${Array.from(magicBytes, b => '0x' + b.toString(16).padStart(2, '0')).join(', ')}]`);
            if (magicBytes[0] === 0x4D) {
                console.log(`[WebFirmwareUploader] .mpy 파일 - 유효한 매직 넘버 'M' 감지`);
            } else {
                console.log(`[WebFirmwareUploader] .mpy 파일 - 매직 넘버 불일치 (버전 차이 또는 손상 가능)`);
            }
        } else {
            console.log(`[WebFirmwareUploader] 기타 파일 형식: ${filename}`);
        }
        
        // 원본 파일 체크섬 계산
        const originalChecksum = this._calculateChecksum(content);
        console.log(`[WebFirmwareUploader] 원본 파일 체크섬: ${originalChecksum}`);
        
        // targetFilename을 사용하여 명령 전송
        await this._sendCommand({
            command: `UPGRADE:FILE_START:${targetFilename}:${fileSize}`,
            channel: 'upgrade'
        });
        await this._delay(100);
        
        // === 전체 파일 Base64 검증용 계산 ===
        console.log(`[VERIFICATION] ===== 전체 파일 Base64 검증 시작 =====`);
        const wholeFileBase64 = this._arrayBufferToBase64Padded(content);
        console.log(`[VERIFICATION] 파일명: ${filename}`);
        console.log(`[VERIFICATION] 원본 크기: ${fileSize}바이트`);
        console.log(`[VERIFICATION] 전체 Base64 길이: ${wholeFileBase64.length}글자`);
        console.log(`[VERIFICATION] 전체 Base64 : ${wholeFileBase64}`);
        //console.log(`[VERIFICATION] 전체 Base64 (마지막 100자): ${wholeFileBase64.substring(Math.max(0, wholeFileBase64.length - 100))}`);
        
        // 2. 파일 데이터를 Base64로 인코딩하여 청크 단위로 전송
        // Base64 패딩 문제 해결을 위해 청크 크기를 3의 배수로 조정
        // 3바이트 -> 4글자 Base64 (패딩 없음)
        // BLE MTU 제한을 고려하여 최대 청크 크기 계산:
        // - 명령어 접두사: "UPGRADE:FILE_DATA:" (18바이트)
        // - Base64 인코딩: 원본의 4/3배
        // - 3의 배수로 조정하여 패딩 없는 Base64 생성
        // - BLE writeValue 512바이트 제한: 360바이트 → 480글자 Base64 → 498바이트 메시지
        const maxRawChunkSize = 360; // 360바이트 (BLE 512바이트 제한 고려)
        const chunkSize = maxRawChunkSize - (maxRawChunkSize % 3); // 3의 배수로 조정: 360바이트
        
        const totalChunks = Math.ceil(fileSize / chunkSize);
        console.log(`[WebFirmwareUploader] ===== 파일 전송 시작 =====`);
        console.log(`[WebFirmwareUploader] 청크 크기: ${chunkSize}바이트 (3의 배수) - BLE 512바이트 제한 고려`);
        console.log(`[WebFirmwareUploader] 총 청크 수: ${totalChunks}개`);
        console.log(`[WebFirmwareUploader] 예상 전송 시간: ${(totalChunks * 100)}ms (100ms/청크)`);
        
        // 청크 개수 20개 제한 경고
        if (totalChunks > 20) {
            console.warn(`[WebFirmwareUploader] ⚠️ 청크 개수가 20개를 초과합니다 (${totalChunks}개)`);
            console.warn(`[WebFirmwareUploader] 보드 펌웨어 제한으로 인해 전송이 실패할 수 있습니다.`);
            console.warn(`[WebFirmwareUploader] 파일 크기: ${fileSize}바이트, 청크 크기: ${chunkSize}바이트`);
        } else {
            console.log(`[WebFirmwareUploader] ✅ 청크 개수가 20개 이하입니다 (${totalChunks}개) - 전송 가능`);
        }
        
        const uint8Array = new Uint8Array(content);
        let totalBase64Length = 0;
        let processedBytes = 0;
        let chunkNumber = 0;
        let successfulChunks = 0;
        
        // === WebREPL 방식 적용: 연속 전송 ===
        try {
            for (let i = 0; i < fileSize; i += chunkSize) {
                const chunk = uint8Array.slice(i, Math.min(i + chunkSize, fileSize));
                processedBytes += chunk.length;
                chunkNumber++;
                
                // 청크 체크섬 계산 (디버깅용)
                const chunkChecksum = this._calculateChecksum(chunk.buffer);
                
                // Base64 인코딩 (개선된 방법)
                const base64Chunk = this._arrayBufferToBase64Padded(chunk);
                totalBase64Length += base64Chunk.length;
                
                // BLE 메시지 크기 확인 및 제한 검증
                const message = `UPGRADE:FILE_DATA:${base64Chunk}`;
                const messageSize = message.length;
                
                // BLE MTU 제한 검증 (360바이트 청크 → 480글자 Base64 → 498바이트 메시지)
                if (messageSize > 512) {
                    throw new Error(`BLE 메시지가 너무 큽니다: ${messageSize}바이트 (512바이트 제한)`);
                }
                
                console.log(`[WebFirmwareUploader] 전송 중 ${chunkNumber}/${totalChunks}: 원본=${chunk.length}바이트, Base64=${base64Chunk.length}바이트, 메시지=${messageSize}바이트`);
                
                // Base64 유효성 검증
                if (!this._isValidBase64(base64Chunk)) {
                    throw new Error(`잘못된 Base64 인코딩: ${base64Chunk.substring(0, 20)}...`);
                }
                
                // Base64 디코딩 테스트 (검증용)
                try {
                    const testDecoded = this._base64ToArrayBuffer(base64Chunk);
                    const testChecksum = this._calculateChecksum(testDecoded);
                    if (testChecksum !== chunkChecksum) {
                        console.error(`[WebFirmwareUploader] 청크 인코딩/디코딩 불일치! 원본: ${chunkChecksum.substring(0,8)}, 디코딩 후: ${testChecksum.substring(0,8)}`);
                    }
                } catch (error) {
                    console.error(`[WebFirmwareUploader] Base64 디코딩 테스트 실패:`, error);
                }
                
                // === 청크 전송 (안정성 우선: ACK 기반) ===
                console.log(`[TX-${chunkNumber}] 전송 시작...`);
                await this._sendCommand({
                    command: message,
                    channel: 'upgrade'
                });
                
                // === ACK 기반 안정성 확보 ===
                console.log(`[TX-${chunkNumber}] ACK 대기 중...`);
                const ack = await this._waitForAck(chunkNumber, 5000);
                if (!ack.success) {
                    console.warn(`[TX-${chunkNumber}] ACK 실패, 재전송 필요:`, ack.message);
                    // 재전송 로직
                    const retryResult = await this._retransmitChunk(message, chunkNumber);
                    if (!retryResult.success) {
                        throw new Error(`청크 ${chunkNumber} 전송 최종 실패: ${retryResult.error}`);
                    }
                }
                console.log(`[TX-${chunkNumber}] 전송 완료 ✓`);
                
                successfulChunks++;
                
                // === 대기 시간 최적화 ===
                // WebREPL 방식을 참고하여 연속 전송하되, BLE 안정성을 위해 최소 대기
                if (chunkNumber < totalChunks) {  // 마지막 청크가 아닌 경우만
                    console.log(`[TX-${chunkNumber}] 100ms 대기 중...`);
                    await this._delay(100);  // 500ms → 100ms로 단축
                }
                
                // 진행률 업데이트 (파일 내 진행률)
                const fileProgress = ((i + chunk.length) / fileSize) * 100;
                console.log(`[WebFirmwareUploader] ${targetFilename} 진행률: ${fileProgress.toFixed(1)}% (${processedBytes}/${fileSize} 바이트)`);
            }
            
            // === 전송 완료 통계 ===
            console.log(`[WebFirmwareUploader] ===== 파일 전송 완료 =====`);
            console.log(`[WebFirmwareUploader] 성공한 청크: ${successfulChunks}/${totalChunks}개`);
            console.log(`[WebFirmwareUploader] 전송 성공률: ${((successfulChunks/totalChunks)*100).toFixed(1)}%`);
            console.log(`[WebFirmwareUploader] 총 원본 크기: ${fileSize}바이트`);
            console.log(`[WebFirmwareUploader] 총 Base64 길이: ${totalBase64Length}글자`);
            console.log(`[WebFirmwareUploader] Base64 오버헤드: ${((totalBase64Length / fileSize) * 100).toFixed(1)}%`);
            
            if (successfulChunks !== totalChunks) {
                throw new Error(`전송 실패: ${successfulChunks}/${totalChunks}개 청크만 전송됨`);
            }
            
        } catch (transmissionError) {
            console.error(`[WebFirmwareUploader] 전송 중 오류 발생:`, transmissionError);
            console.error(`[WebFirmwareUploader] 실패 지점: 청크 ${chunkNumber}/${totalChunks}`);
            console.error(`[WebFirmwareUploader] 성공한 청크: ${successfulChunks}개`);
            throw transmissionError;
        }
        
        // 3. 파일 전송 완료 알림
        await this._sendCommand({
            command: `UPGRADE:FILE_END:${targetFilename}`,
            channel: 'upgrade'
        });
        await this._delay(500);  // 100ms에서 500ms로 증가
        
        console.log(`[WebFirmwareUploader] 파일 업로드 완료: ${targetFilename} (원본: ${filename})`);
    }
    
    /**
     * 업로드 완료 처리
     */
    async _finishUpload() {
        // 모든 파일 전송 완료, 실제 업그레이드 실행
        await this._sendCommand({
            command: 'UPGRADE:COMMIT',
            channel: 'upgrade'
        });
        await this._delay(1000);
        
        this._updateStatus('펌웨어 설치 중... 보드가 재시작됩니다.');
    }
    
    /**
     * 🧪 테스트 모드: temp 저장만 실행 (commit 하지 않음)
     */
    async startTempUpload() {
        console.log('[WebFirmwareUploader] === temp 저장 모드 시작 ===');
        
        if (this.isUploading) {
            throw new Error('이미 업로드가 진행중입니다');
        }
        
        if (this.firmwareFiles.size === 0) {
            throw new Error('업로드할 파일이 없습니다');
        }
        
        this.isUploading = true;
        
        try {
            // 1. 파일 수신 모드 진입
            await this._enterFileUploadMode();
            
            // 2. 파일들을 temp에 저장 (commit 없음)
            this._updateStatus('temp 디렉토리에 파일 저장 중...');
            
            const totalFiles = this.firmwareFiles.size;
            let completedFiles = 0;
            
            for (const [filename, content] of this.firmwareFiles) {
                // 파일 경로 결정 (표시용)
                let displayFilename = filename;
                if (filename.endsWith('.mpy') && !filename.startsWith('lib/')) {
                    displayFilename = `lib/${filename}`;
                }
                
                this._updateStatus(`temp 저장 중: ${displayFilename}`);
                
                await this._uploadSingleFile(filename, content);
                
                completedFiles++;
                const progress = (completedFiles / totalFiles) * 100;
                this._updateProgress(progress);
                
                // 파일 간 짧은 대기
                await this._delay(100);
            }
            
            this._updateStatus('모든 파일이 temp 디렉토리에 저장되었습니다!');
            this._updateProgress(100);
            console.log('[WebFirmwareUploader] === temp 저장 완료 ===');
            
            if (this.onStatus) {
                this.onStatus('temp 저장 완료! commit 버튼을 눌러 적용하세요');
            }
            
        } catch (error) {
            this._updateError('temp 저장 실패: ' + error.message);
            throw error;
        } finally {
            this.isUploading = false;
        }
    }
    
    /**
     * 🧪 테스트 모드: commit 실행 (temp → 실제 적용)
     */
    async commitUpload() {
        console.log('[WebFirmwareUploader] === commit 시작 ===');
        
        if (this.isUploading) {
            throw new Error('업로드가 진행중입니다');
        }
        
        this.isUploading = true;
        
        try {
            this._updateStatus('commit 실행 중...');
            
            // UPGRADE:COMMIT 명령 전송
            await this._sendCommand({
                command: 'UPGRADE:COMMIT',
                channel: 'upgrade'
            });
            
            this._updateStatus('commit 완료! 보드가 재시작됩니다...');
            console.log('[WebFirmwareUploader] === commit 완료 ===');
            
            // 잠시 대기 후 완료 처리
            await this._delay(1000);
            
            if (this.onComplete) {
                this.onComplete();
            }
            
        } catch (error) {
            this._updateError('commit 실패: ' + error.message);
            throw error;
        } finally {
            this.isUploading = false;
        }
    }
    
    /**
     * 🔬 단계별 테스트: 2단계 - 백업만 실행
     */
    async runStep2Backup() {
        console.log('[WebFirmwareUploader] === 2단계: 백업 시작 ===');
        
        if (this.isUploading) {
            throw new Error('업로드가 진행중입니다');
        }
        
        this.isUploading = true;
        
        try {
            // ESP32에 백업 명령만 전송하고, 진행 상황은 ESP32에서 오는 메시지로만 표시
            await this._sendCommand({
                command: 'UPGRADE:STEP2_BACKUP',
                channel: 'upgrade'
            });
            
            console.log('[WebFirmwareUploader] === 2단계: 백업 명령 전송 완료 ===');
            
        } catch (error) {
            this._updateError('2단계 백업 실패: ' + error.message);
            throw error;
        } finally {
            this.isUploading = false;
        }
    }
    
    /**
     * 🔬 단계별 테스트: 3단계 - temp 파일 적용만 실행
     */
    async runStep3Apply() {
        console.log('[WebFirmwareUploader] === 3단계: 적용 시작 ===');
        
        if (this.isUploading) {
            throw new Error('업로드가 진행중입니다');
        }
        
        this.isUploading = true;
        
        try {
            this._updateStatus('3단계: temp 파일을 실제 위치에 적용 중...');
            
            // UPGRADE:STEP3_APPLY 명령 전송
            await this._sendCommand({
                command: 'UPGRADE:STEP3_APPLY',
                channel: 'upgrade'
            });
            
            this._updateStatus('3단계: 파일 적용 완료!');
            console.log('[WebFirmwareUploader] === 3단계: 적용 완료 ===');
            
            // 잠시 대기
            await this._delay(500);
            
        } catch (error) {
            this._updateError('3단계 적용 실패: ' + error.message);
            throw error;
        } finally {
            this.isUploading = false;
        }
    }
    
    /**
     * 🔬 단계별 테스트: 4단계 - temp 정리 및 재시작
     */
    async runStep4Cleanup() {
        console.log('[WebFirmwareUploader] === 4단계: 정리&재시작 시작 ===');
        
        if (this.isUploading) {
            throw new Error('업로드가 진행중입니다');
        }
        
        this.isUploading = true;
        
        try {
            this._updateStatus('4단계: temp 파일 정리 및 재시작 중...');
            
            // UPGRADE:STEP4_CLEANUP 명령 전송
            await this._sendCommand({
                command: 'UPGRADE:STEP4_CLEANUP',
                channel: 'upgrade'
            });
            
            this._updateStatus('4단계: 정리 완료! 보드가 재시작됩니다...');
            console.log('[WebFirmwareUploader] === 4단계: 정리&재시작 완료 ===');
            
            // 잠시 대기 후 완료 처리
            await this._delay(1000);
            
            if (this.onComplete) {
                this.onComplete();
            }
            
        } catch (error) {
            this._updateError('4단계 정리&재시작 실패: ' + error.message);
            throw error;
        } finally {
            this.isUploading = false;
        }
    }
    
    /**
     * 🔍 ESP32 상태 확인
     */
    async checkUpgradeStatus() {
        console.log('[WebFirmwareUploader] === ESP32 상태 확인 시작 ===');
        
        try {
            this._updateStatus('ESP32 상태 확인 중...');
            
            // === BLE 재연결 시 ACK 핸들러 재등록 보장 ===
            if (this.bleManager && this.bleManager.isConnected) {
                console.log('[WebFirmwareUploader] 상태 확인 전 ACK 핸들러 강제 재등록');
                this._registerAckHandler(true); // 강제 재등록
                
                // ACK 핸들러 등록 후 잠시 대기
                await this._delay(300);
            } else {
                throw new Error('BLE 연결이 필요합니다.');
            }
            
            // UPGRADE:STATUS 명령 전송
            await this._sendCommand({
                command: 'UPGRADE:STATUS',
                channel: 'upgrade'
            });
            
            console.log('[WebFirmwareUploader] === 상태 확인 명령 전송 완료 ===');
            
        } catch (error) {
            this._updateError('상태 확인 실패: ' + error.message);
            throw error;
        }
    }
    
    /**
     * 🔍 상태 확인 응답 처리
     */
    _handleStatusResponse(message) {
        try {
            console.log('[STATUS] 상태 응답 처리:', message);
            
            if (message.startsWith('TEMP_FILES:')) {
                // TEMP_FILES:count:file1:size1,file2:size2,...
                const parts = message.split(':');
                const tempCount = parseInt(parts[1]);
                const tempFiles = parts.length > 2 ? parts.slice(2).join(':') : '';
                
                if (tempCount > 0) {
                    this._updateStatus(`📁 temp 파일 발견: ${tempCount}개 파일 (${tempFiles})`);
                } else {
                    this._updateStatus('📁 temp 파일 없음');
                }
            }
            else if (message.startsWith('BACKUP_FILES:')) {
                // BACKUP_FILES:count:file1:size1,file2:size2,...
                const parts = message.split(':');
                const backupCount = parseInt(parts[1]);
                const backupFiles = parts.length > 2 ? parts.slice(2).join(':') : '';
                
                if (backupCount > 0) {
                    this._updateStatus(`💾 backup 파일 발견: ${backupCount}개 파일 (${backupFiles})`);
                } else {
                    this._updateStatus('💾 backup 파일 없음');
                }
            }
            else if (message.startsWith('STATUS_ANALYSIS:')) {
                // STATUS_ANALYSIS:상태:설명
                const parts = message.split(':');
                const status = parts[1];
                const description = parts.slice(2).join(':');
                
                this._updateStatus(`🔍 상태 분석: ${description}`);
                
                // 상태별 권장 사항 안내
                if (status === 'STEP2_READY') {
                    this._updateStatus('💡 권장: 2단계(백업) 버튼을 클릭하세요', 'info');
                } else if (status === 'STEP3_READY') {
                    this._updateStatus('💡 권장: 3단계(적용) 버튼을 클릭하세요', 'info');
                } else if (status === 'ROLLBACK_READY') {
                    this._updateStatus('💡 권장: 업그레이드에 문제가 있으면 롤백 버튼을 클릭하여 이전 버전으로 복원하세요', 'info');
                } else if (status === 'CLEAN') {
                    this._updateStatus('💡 상태: 새로운 업그레이드를 시작할 수 있습니다', 'info');
                }
            }
            else if (message.startsWith('MEMORY_FREE:')) {
                const memoryKB = parseInt(message.split(':')[1]) / 1024;
                this._updateStatus(`🧠 메모리: ${memoryKB.toFixed(1)}KB 사용 가능`);
            }
            else if (message === 'STATUS_CHECK_COMPLETE') {
                this._updateStatus('✅ ESP32 상태 확인 완료', 'success');
            }
            // === 🔬 백업 관련 상세 메시지 처리 ===
            else if (message.startsWith('STEP2_BACKUP_START')) {
                this._updateStatus('=== 🔬 상세 방식: 2단계 백업 시작 ===', 'info');
            }
            else if (message.startsWith('BACKUP_PHASE:')) {
                // BACKUP_PHASE:단계설명
                const phaseDescription = message.substring(13); // 'BACKUP_PHASE:' 제거
                this._updateStatus(`📋 ${phaseDescription}`, 'info');
            }
            else if (message.startsWith('BACKUP_FILE_START:')) {
                // BACKUP_FILE_START:1/7:boot.py
                const parts = message.split(':');
                if (parts.length >= 3) {
                    const progress = parts[1]; // "1/7"
                    const filename = parts[2]; // "boot.py"
                    this._updateStatus(`📁 백업 중 (${progress}): ${filename}`, 'progress');
                }
            }
            else if (message.startsWith('BACKUP_FILE_COMPLETE:')) {
                // BACKUP_FILE_COMPLETE:1/7:boot.py
                const parts = message.split(':');
                if (parts.length >= 3) {
                    const progress = parts[1]; // "1/7"
                    const filename = parts[2]; // "boot.py"
                    this._updateStatus(`✅ 백업 완료 (${progress}): ${filename}`, 'success');
                }
            }
            else if (message.startsWith('BACKUP_DETAIL:')) {
                // BACKUP_DETAIL:filename:상태:설명
                const parts = message.split(':');
                if (parts.length >= 4) {
                    const filename = parts[1];
                    const status = parts[2];
                    const description = parts[3];
                    
                    if (status === '시작') {
                        this._updateStatus(`🔄 ${filename}: ${description}`, 'progress');
                    } else if (status === '복사 시작') {
                        this._updateStatus(`📋 ${filename}: 복사 중...`, 'progress');
                    } else if (status === '복사 완료') {
                        this._updateStatus(`✅ ${filename}: 백업 성공`, 'success');
                    } else if (status === '오류') {
                        this._updateStatus(`❌ ${filename}: ${description}`, 'error');
                    } else {
                        this._updateStatus(`📄 ${filename}: ${description}`, 'info');
                    }
                }
            }
            else if (message.startsWith('BACKUP_VERIFICATION:')) {
                // BACKUP_VERIFICATION:성공:7:신규:2:추가:0 (변경된 형식)
                const parts = message.split(':');
                if (parts.length >= 7) {
                    const successCount = parseInt(parts[2]);
                    const newFilesCount = parseInt(parts[4]);
                    const extraCount = parseInt(parts[6]);
                    
                    if (newFilesCount === 0) {
                        this._updateStatus(`✅ 백업 검증 성공: ${successCount}개 파일 모두 백업됨`, 'success');
                    } else {
                        this._updateStatus(`ℹ️ 백업 검증 완료: ${successCount}개 백업, ${newFilesCount}개 신규 파일`, 'info');
                    }
                }
            }
            else if (message.startsWith('BACKUP_NEW_FILES:')) {
                const newFilesList = message.substring(18); // 'BACKUP_NEW_FILES:' 제거
                if (newFilesList && newFilesList.trim() !== '') {
                    // 쉼표로 구분된 파일 목록을 줄바꿈으로 표시
                    const files = newFilesList.split(',');
                    if (files.length <= 3) {
                        // 파일이 적으면 한 줄에 표시
                        this._updateStatus(`📄 신규 파일: ${files.join(', ')}`, 'info');
                    } else {
                        // 파일이 많으면 개수만 표시
                        this._updateStatus(`📄 신규 파일 ${files.length}개 (기존 보드에 없던 파일들)`, 'info');
                    }
                }
            }
            else if (message.startsWith('BACKUP_VERIFICATION_SUCCESS:')) {
                const description = message.substring(29); // 'BACKUP_VERIFICATION_SUCCESS:' 제거
                this._updateStatus(`✅ 검증 성공: ${description}`, 'success');
            }
            else if (message.startsWith('BACKUP_VERIFICATION_INFO:')) {
                const description = message.substring(26); // 'BACKUP_VERIFICATION_INFO:' 제거
                this._updateStatus(`ℹ️ 검증 정보: ${description}`, 'info');
            }
            else if (message.startsWith('BACKUP_VERIFICATION_WARNING:')) {
                const description = message.substring(29); // 'BACKUP_VERIFICATION_WARNING:' 제거
                // 숫자가 빠진 경우 처리
                if (description.includes('개 파일')) {
                    this._updateStatus(`⚠️ 검증 경고: ${description}`, 'warning');
                } else {
                    this._updateStatus(`⚠️ 검증 경고: ${description}`, 'warning');
                }
            }
            else if (message.startsWith('STEP2_BACKUP_SUCCESS:')) {
                const description = message.substring(22); // 'STEP2_BACKUP_SUCCESS:' 제거
                this._updateStatus(`🎉 2단계: 백업 완료!`, 'success');
                this._updateStatus(`=== 🔬 2단계 완료! 3단계 "적용" 버튼 활성화 ===`, 'success');
            }
            else if (message.startsWith('STEP2_BACKUP_COMPLETE:')) {
                // STEP2_BACKUP_COMPLETE:성공:7:실패:0
                const parts = message.split(':');
                if (parts.length >= 5) {
                    const successCount = parts[2];
                    const failureCount = parts[4];
                    this._updateStatus(`📊 백업 완료 통계: 성공 ${successCount}개, 실패 ${failureCount}개`, 'info');
                }
            }
            
        } catch (error) {
            console.error('[STATUS] 상태 응답 처리 실패:', error);
            this._updateError('상태 응답 처리 실패: ' + error.message);
        }
    }
    
    /**
     * ArrayBuffer를 올바른 패딩이 있는 Base64로 변환 (개선된 함수)
     */
    _arrayBufferToBase64Padded(buffer) {
        try {
            // === Base64 인코딩 3단계 과정 ===
            // 1단계: ArrayBuffer → Uint8Array (바이트 배열)
            const bytes = new Uint8Array(buffer);
            const len = bytes.byteLength;
            
            console.log(`[Base64Debug] 1단계: ArrayBuffer(${buffer.byteLength}바이트) → Uint8Array(${len}개)`);
            
            // 2단계: Uint8Array → 바이너리 문자열
            // window.btoa()는 바이너리 문자열만 처리 가능하므로 필수 변환
            // 각 바이트(0-255)를 해당하는 문자로 변환
            let binary = '';
            
            // 성능 최적화: 작은 청크로 나누어 처리 (메모리 절약)
            for (let i = 0; i < len; i ++) {
                // const end = Math.min(i + chunkSize, len);
                // const chunk = bytes.subarray(i, end);
                
                // String.fromCharCode.apply 사용 (성능 개선)
                try {
                    binary += String.fromCharCode(bytes[i]);
                } catch (e) {
                    // apply 스택 오버플로우 시 fallback
                    console.warn('[Base64Debug] apply 실패, 개별 변환 사용');
                    // for (let j = 0; j < chunk.length; j++) {
                    //     binary += String.fromCharCode(chunk[j]);
                    // }
                }
            }
            console.log(`[Base64Debug] 2단계: Uint8Array → 바이너리문자열(${binary.length}글자)`);
            
            // 3단계: 바이너리 문자열 → Base64
            // window.btoa(): Binary to ASCII (Base64 인코딩)
            const base64 = window.btoa(binary);
            
            console.log(`[Base64Debug] 3단계: 바이너리문자열 → Base64(${base64.length}글자)`);
            console.log(`[Base64Debug] *** 실제 Base64 내용 확인 ***`);
            console.log(`[Base64Debug] Base64 전체: "${base64}"`);
            console.log(`[Base64Debug] Base64 첫 50자: "${base64.substring(0, 50)}"`);
            console.log(`[Base64Debug] Base64 마지막 50자: "${base64.substring(Math.max(0, base64.length - 50))}"`);
            
            // === 왜 이런 3단계 과정이 필요한가? ===
            // 1. window.btoa()는 ArrayBuffer를 직접 처리할 수 없음
            // 2. JavaScript 내장 함수는 문자열 기반으로 설계됨
            // 3. 브라우저 호환성 (모든 브라우저에서 동작)
            // 4. 표준 Base64 인코딩 알고리즘 활용
            
            // Base64 유효성 확인 및 패딩 보정
            let paddedBase64 = base64;
            const remainder = paddedBase64.length % 4;
            if (remainder !== 0) {
                const paddingLength = 4 - remainder;
                paddedBase64 += '='.repeat(paddingLength);
                console.log(`[Base64Debug] 패딩 추가: ${paddingLength}개 ('=' 문자)`);
            }
            
            // 변환 효율성 로그
            const efficiency = (base64.length / len * 100).toFixed(1);
            console.log(`[Base64Debug] 변환 효율성: ${len}바이트 → ${base64.length}글자 (${efficiency}% 증가)`);
            console.log(`[Base64Debug] 이론적 Base64 크기: ${Math.ceil(len * 4 / 3)}글자`);
            
            return paddedBase64;
            
        } catch (error) {
            console.error('[WebFirmwareUploader] Base64 인코딩 실패:', error);
            console.error('[WebFirmwareUploader] 문제 버퍼 크기:', buffer.byteLength);
            console.error('[WebFirmwareUploader] 버퍼 내용 (처음 10바이트):', new Uint8Array(buffer).slice(0, 10));
            throw new Error('Base64 인코딩 실패: ' + error.message);
        }
    }
    
    /**
     * 대안: 현대적 Base64 인코딩 (참고용)
     * 구형 브라우저에서는 동작하지 않을 수 있음
     */
    _arrayBufferToBase64Modern(buffer) {
        try {
            // Spread operator 사용 (ES6+)
            const base64 = btoa(String.fromCharCode(...new Uint8Array(buffer)));
            return base64;
        } catch (error) {
            // 스택 오버플로우 시 기존 방법으로 fallback
            console.warn('[Base64Debug] 현대적 방법 실패, 기존 방법 사용');
            return this._arrayBufferToBase64Padded(buffer);
        }
    }
    
    /**
     * Base64를 ArrayBuffer로 디코딩 (검증용)
     */
    _base64ToArrayBuffer(base64String) {
        try {
            const binaryString = window.atob(base64String);
            const bytes = new Uint8Array(binaryString.length);
            for (let i = 0; i < binaryString.length; i++) {
                bytes[i] = binaryString.charCodeAt(i);
            }
            return bytes.buffer;
        } catch (error) {
            throw new Error('Base64 디코딩 실패: ' + error.message);
        }
    }
    
    /**
     * 간단한 체크섬 계산 (MicroPython과 동일한 방식)
     */
    _calculateChecksum(buffer) {
        try {
            const bytes = new Uint8Array(buffer);
            let sum = 0;
            for (let i = 0; i < bytes.length; i++) {
                sum = (sum + bytes[i]) & 0xFFFFFFFF;  // 32비트 오버플로우 방지
            }
            return sum.toString(16).padStart(8, '0');
        } catch (error) {
            console.error('[WebFirmwareUploader] 체크섬 계산 실패:', error);
            return '00000000';
        }
    }
    
    /**
     * Base64 문자열 유효성 검증
     */
    _isValidBase64(str) {
        try {
            // Base64 정규표현식 검증
            const base64Regex = /^[A-Za-z0-9+/]*={0,2}$/;
            if (!base64Regex.test(str)) {
                return false;
            }
            
            // 길이가 4의 배수인지 확인
            if (str.length % 4 !== 0) {
                return false;
            }
            
            // 디코딩 테스트
            window.atob(str);
            return true;
        } catch (error) {
            return false;
        }
    }
    
    /**
     * BLE로 명령 전송 (BLEManager의 sendCommand 사용)
     */
    async _sendCommand(params) {
        // 매개변수 형태 확인 및 정규화
        let command, channel;
        
        if (typeof params === 'string') {
            // 기존 방식: 문자열만 전달된 경우
            command = params;
            channel = 'upgrade';
        } else if (typeof params === 'object' && params.command) {
            // 새로운 방식: 객체로 전달된 경우
            command = params.command;
            channel = params.channel || 'upgrade';
        } else {
            throw new Error('잘못된 매개변수 형태입니다.');
        }
        
        console.log(`[WebFirmwareUploader] _sendCommand 진입: command="${command}", channel="${channel}"`);
        
        if (!this.bleManager || !this.bleManager.isConnected) {
            throw new Error('BLE 연결이 없습니다.');
        }

        try {
            // 디버그 로그 추가
            console.log(`[WebFirmwareUploader] BLEManager를 통한 명령 전송 시작`);
            console.log(`[WebFirmwareUploader] 전달할 매개변수: command="${command}", channel="${channel}"`);
            
            // BLEManager의 sendCommand 확인
            console.log(`[WebFirmwareUploader] BLEManager 객체:`, this.bleManager);
            console.log(`[WebFirmwareUploader] sendCommand 메서드 존재:`, typeof this.bleManager.sendCommand);
            
            // BLEManager의 sendCommand를 개별 매개변수로 호출
            console.log(`[WebFirmwareUploader] ===== 호출 직전 검증 =====`);
            console.log(`[WebFirmwareUploader] 첫 번째 매개변수 (command): "${command}"`);
            console.log(`[WebFirmwareUploader] 두 번째 매개변수 (channel): "${channel}"`);
            console.log(`[WebFirmwareUploader] typeof command: ${typeof command}`);
            console.log(`[WebFirmwareUploader] typeof channel: ${typeof channel}`);
            
            // 강제로 매개변수 순서 고정
            const param1 = String(command);
            const param2 = String(channel);
            console.log(`[WebFirmwareUploader] 강제 문자열 변환 후:`);
            console.log(`[WebFirmwareUploader] param1: "${param1}"`);
            console.log(`[WebFirmwareUploader] param2: "${param2}"`);
            
            const result = await this.bleManager.sendCommand(param1, param2);
            
            console.log(`[WebFirmwareUploader] 명령 전송 성공: ${command}, 결과:`, result);
            return result;
        } catch (error) {
            console.error(`[WebFirmwareUploader] 명령 전송 실패:`, error);
            console.error(`[WebFirmwareUploader] 오류 상세:`, {
                name: error.name,
                message: error.message,
                stack: error.stack
            });
            throw error;
        }
    }
    
    /**
     * 지연 함수
     */
    _delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
    
    /**
     * 상태 업데이트
     */
    _updateStatus(message) {
        console.log(`[WebFirmwareUploader] ${message}`);
        if (this.onStatus) {
            this.onStatus(message);
        }
    }
    
    /**
     * 진행률 업데이트
     */
    _updateProgress(percent) {
        this.uploadProgress = percent;
        console.log(`[WebFirmwareUploader] 진행률: ${percent.toFixed(1)}%`);
        if (this.onProgress) {
            this.onProgress(percent);
        }
    }
    
    /**
     * 오류 업데이트
     */
    _updateError(message) {
        console.error(`[WebFirmwareUploader] ${message}`);
        if (this.onError) {
            this.onError(message);
        }
    }
    
    /**
     * 업로드 중단
     */
    async cancelUpload() {
        if (this.isUploading) {
            this.isUploading = false;
            this._updateStatus('업로드 중단 중...');
            
            // 업그레이드 중단 명령 전송
            try {
                await this._sendCommand('UPGRADE:ABORT');
                await this._delay(200);
            } catch (error) {
                console.warn('업그레이드 중단 명령 전송 실패:', error);
            }
            
            this._updateStatus('업로드가 중단되었습니다.');
        }
    }
    
    /**
     * 보드 재시작 (BLE 명령으로 변경)
     */
    async restartBoard() {
        try {
            this._updateStatus('보드 재시작 중...');
            await this._sendCommand('import machine; machine.reset()');
            await this._delay(1000);
            this._updateStatus('보드가 재시작되었습니다.');
        } catch (error) {
            this._updateError('보드 재시작 실패: ' + error.message);
        }
    }
    
    /**
     * 기존 버전 롤백 (백업 파일에서 복원)
     */
    async rollbackFirmware() {
        try {
            this._updateStatus('기존 버전 롤백 시작...');
            await this._sendCommand('UPGRADE:ROLLBACK');
            await this._delay(2000);
            this._updateStatus('롤백 완료! 보드가 재시작됩니다.');
        } catch (error) {
            this._updateError('롤백 실패: ' + error.message);
        }
    }
    
    /**
     * ACK 핸들러를 BLEManager의 중앙 데이터 처리 시스템에 등록
     */
    _registerAckHandler(forceRegister = false) {
        if (!this.bleManager) {
            console.error('[ACK] BLEManager가 없습니다.');
            return;
        }

        // 중복 등록 방지 (강제 등록 모드가 아닌 경우에만)
        if (!forceRegister && this.ackHandlerRegistered) {
            console.log('[ACK] ACK 핸들러가 이미 등록되어 있습니다. 중복 등록을 방지합니다.');
            console.log('[ACK] 강제 재등록이 필요하면 forceRegister=true로 호출하세요.');
            return;
        }

        if (forceRegister) {
            console.log('[ACK] ===== 강제 재등록 모드 =====');
            // 기존 핸들러 정리
            this._cleanupAckHandlers();
            this.ackHandlerRegistered = false; // 강제 초기화
        }

        console.log('[ACK] BLEManager 중앙 데이터 처리 시스템에 ACK 핸들러 등록 시작');
        
        // 연결 상태 엄격 확인
        if (!this.bleManager.isConnected) {
            console.warn('[ACK] BLE가 연결되지 않았습니다. ACK 핸들러 등록을 중단합니다.');
            return;
        }
        
        // GATT 서버 확인
        if (!this.bleManager.server) {
            console.warn('[ACK] GATT 서버가 없습니다. ACK 핸들러 등록을 중단합니다.');
            return;
        }

        console.log('[ACK] BLE 연결 및 GATT 서버 확인 완료 - ACK 핸들러 등록 진행');

        // **단일 경로 사용: BLEManager의 onDataReceived만 사용**
        this.bleManager.onDataReceived((dataObj) => {
            console.log('[ACK] onDataReceived 콜백 호출됨:', dataObj);
            
            const { characteristicUUID, data } = dataObj;
            
            // UPGRADE 특성에서 오는 데이터만 처리
            if (characteristicUUID === UPGRADE_CHARACTERISTIC) {
                console.log('[ACK] UPGRADE 특성 데이터 수신 확인:', {
                    characteristicUUID,
                    dataType: typeof data,
                    data: data
                });
                
                // 이벤트 객체 형태로 변환하여 기존 핸들러와 호환
                const mockEvent = {
                    target: {
                        value: data
                    }
                };
                
                // 데이터를 ACK 핸들러로 전달
                this._handleAckNotification(mockEvent);
            } else {
                console.log('[ACK] 다른 특성 데이터 무시:', characteristicUUID);
            }
        });

        // === 이중 안전장치 복원: UPGRADE 특성 직접 알림도 등록 ===
        // 보드 응답을 확실히 받기 위해 두 가지 경로 모두 사용
        console.log('[ACK] 이중 안전장치: UPGRADE 특성 직접 알림 등록 시도');
        try {
            this.bleManager.startNotifications(UPGRADE_CHARACTERISTIC, (value) => {
                console.log('[ACK] 직접 UPGRADE 특성 알림 수신:', value);
                
                const mockEvent = {
                    target: { value: value }
                };
                
                this._handleAckNotification(mockEvent);
            }).then(() => {
                console.log('[ACK] UPGRADE 특성 직접 알림 시작 성공');
            }).catch(error => {
                console.warn('[ACK] UPGRADE 특성 직접 알림 시작 실패 (BLE 상태 문제):', error.message);
            });
        } catch (error) {
            console.warn('[ACK] UPGRADE 특성 직접 알림 등록 오류 (BLE 상태 문제):', error.message);
        }

        // === 이중 안전장치 완료 ===
        // onDataReceived와 startNotifications 모두 등록하여 보드 응답을 확실히 수신
        console.log('[ACK] 이중 안전장치 등록 완료 - 보드 응답 수신 보장');

        // 등록 완료 플래그 설정
        this.ackHandlerRegistered = true;
        console.log('[ACK] BLEManager 중앙 데이터 처리 시스템에 ACK 핸들러 등록 완료');
        
        if (forceRegister) {
            console.log('[ACK] ===== 강제 재등록 완료 =====');
        }
    }
    
    /**
     * 기존 ACK 핸들러들 정리
     */
    _cleanupAckHandlers() {
        try {
            console.log('[ACK] 기존 ACK 핸들러 정리 시작');
            
            // BLEManager의 onDataReceived는 단일 콜백이므로 null로 설정하여 정리
            if (this.bleManager) {
                console.log('[ACK] BLEManager onDataReceived 콜백을 null로 설정');
                this.bleManager.onDataReceived(null);
                console.log('[ACK] BLEManager onDataReceived 콜백 정리 완료');
            }
            
            // UPGRADE 특성의 직접 알림 정리 (실제 메서드가 있는 경우에만)
            if (this.bleManager && typeof this.bleManager.stopNotifications === 'function') {
                try {
                    this.bleManager.stopNotifications(UPGRADE_CHARACTERISTIC);
                    console.log('[ACK] UPGRADE 특성 직접 알림 정지 완료');
                } catch (error) {
                    console.warn('[ACK] UPGRADE 특성 직접 알림 정지 실패:', error.message);
                }
            } else {
                console.log('[ACK] stopNotifications 메서드가 없어서 직접 알림 정지 건너뜀');
            }
            
            console.log('[ACK] 기존 ACK 핸들러 정리 완료');
            
        } catch (error) {
            console.warn('[ACK] ACK 핸들러 정리 중 오류:', error.message);
        }
    }
    
    /**
     * ACK 노티피케이션 처리
     */
    _handleAckNotification(event) {
        try {
            console.log('[ACK] _handleAckNotification 호출됨:', event);
            
            let value = event.target.value;
            let message = '';
            
            // 다양한 데이터 형식 처리
            if (value instanceof ArrayBuffer) {
                const decoder = new TextDecoder();
                message = decoder.decode(value);
                console.log('[ACK] ArrayBuffer에서 메시지 디코딩:', message);
            } else if (value instanceof DataView) {
                const decoder = new TextDecoder();
                message = decoder.decode(value);
                console.log('[ACK] DataView에서 메시지 디코딩:', message);
            } else if (value && value.buffer instanceof ArrayBuffer) {
                const decoder = new TextDecoder();
                message = decoder.decode(value);
                console.log('[ACK] TypedArray에서 메시지 디코딩:', message);
            } else if (typeof value === 'string') {
                message = value;
                console.log('[ACK] 문자열 메시지 직접 사용:', message);
            } else {
                console.warn('[ACK] 알 수 없는 데이터 형식:', typeof value, value);
                message = String(value || '');
            }
            
            // === 이중 안전장치로 인한 중복 메시지 방지 ===
            if (!this.lastProcessedMessages) {
                this.lastProcessedMessages = new Map();
            }
            
            const now = Date.now();
            const messageKey = message;
            const lastProcessed = this.lastProcessedMessages.get(messageKey);
            
            // 같은 메시지가 100ms 이내에 처리되었다면 중복으로 간주하여 무시
            if (lastProcessed && (now - lastProcessed) < 100) {
                console.log('[ACK] 중복 메시지 감지하여 무시:', message);
                return;
            }
            
            // 현재 메시지 처리 시간 기록
            this.lastProcessedMessages.set(messageKey, now);
            
            // 오래된 기록들 정리 (메모리 절약)
            for (let [key, timestamp] of this.lastProcessedMessages.entries()) {
                if (now - timestamp > 5000) { // 5초 이상 된 기록 삭제
                    this.lastProcessedMessages.delete(key);
                }
            }
            
            console.log('[ACK] 최종 처리 메시지:', {
                originalType: typeof value,
                messageLength: message.length,
                message: message,
                bytes: value instanceof ArrayBuffer ? Array.from(new Uint8Array(value)) : 'N/A'
            });
            
            // ACK 메시지 파싱: "CHUNK_ACK:chunk_id:status:message"
            if (message.startsWith('CHUNK_ACK:')) {
                console.log('[ACK] CHUNK_ACK 메시지 감지:', message);
                const parts = message.split(':');
                console.log('[ACK] 메시지 파싱 결과:', parts);
                
                if (parts.length >= 4) {
                    const chunkId = parseInt(parts[1]);
                    const status = parts[2]; // "OK" or "ERROR"
                    const ackMessage = parts.slice(3).join(':'); // 나머지 메시지
                    
                    const ackData = {
                        success: status === 'OK',
                        message: ackMessage,
                        timestamp: Date.now(),
                        originalMessage: message
                    };
                    
                    // ACK 데이터 저장
                    this.ackSettings.ackReceived.set(chunkId, ackData);
                    
                    console.log(`[ACK] 청크 ${chunkId} ACK 저장 완료:`, ackData);
                    console.log(`[ACK] 현재 ACK 맵 크기:`, this.ackSettings.ackReceived.size);
                    console.log(`[ACK] 현재 ACK 맵 키들:`, Array.from(this.ackSettings.ackReceived.keys()));
                } else {
                    console.warn('[ACK] CHUNK_ACK 메시지 형식 오류:', parts);
                }
            } 
            // === 🔍 상태 확인 응답 처리 ===
            else if (message.startsWith('STATUS_')) {
                console.log('[STATUS] 상태 확인 응답:', message);
                this._handleStatusResponse(message);
            }
            // === 🔬 백업 및 업그레이드 관련 메시지 처리 ===
            else if (message.startsWith('BACKUP_') || 
                     message.startsWith('STEP2_') || 
                     message.startsWith('STEP3_') || 
                     message.startsWith('STEP4_') ||
                     message.startsWith('TEMP_') ||
                     message.startsWith('APPLY_') ||
                     message.startsWith('CLEANUP_') ||
                     message.startsWith('RESTART_')) {
                console.log('[UPGRADE] 업그레이드 메시지:', message);
                this._handleStatusResponse(message);
            }
            else if (message.includes('CHUNK_ACK')) {
                console.warn('[ACK] CHUNK_ACK 포함하지만 시작하지 않는 메시지:', message);
            } else {
                console.log('[ACK] 비 CHUNK_ACK 메시지 (일반 응답):', message);
            }
            
        } catch (error) {
            console.error('[ACK] 노티피케이션 처리 실패:', error);
            console.error('[ACK] 이벤트 데이터:', event);
            console.error('[ACK] 스택 추적:', error.stack);
        }
    }
    
    // ===== ACK 기반 확인 통신 함수들 =====
    
    /**
     * 청크 ACK 대기
     */
    async _waitForAck(chunkNumber, timeout = 5000) {
        const startTime = Date.now();
        
        while (Date.now() - startTime < timeout) {
            // ACK 수신 확인
            if (this.ackSettings.ackReceived.has(chunkNumber)) {
                const ackData = this.ackSettings.ackReceived.get(chunkNumber);
                
                // 사용된 ACK 데이터 삭제 (메모리 정리)
                this.ackSettings.ackReceived.delete(chunkNumber);
                
                console.log(`[ACK] 청크 ${chunkNumber} ACK 확인: ${ackData.success ? 'SUCCESS' : 'FAILED'}`);
                return ackData;
            }
            
            // 50ms 간격으로 확인
            await this._delay(50);
        }
        
        // 타임아웃 발생
        console.warn(`[ACK] 청크 ${chunkNumber} ACK 타임아웃 (${timeout}ms)`);
        return {
            success: false,
            message: 'ACK timeout',
            timeout: true
        };
    }
    
    /**
     * 청크 재전송
     */
    async _retransmitChunk(message, chunkNumber, retryCount = 1) {
        try {
            console.log(`[ACK] 청크 ${chunkNumber} 재전송 시도 ${retryCount}/${this.ackSettings.maxRetries}`);
            
            // 재전송 통계 업데이트
            this.transmissionStats.retransmissions++;
            
            // 재전송 전 추가 대기 (안정성 향상)
            await this._delay(200 * retryCount); // 점진적 백오프
            
            // 청크 재전송
            await this._sendCommand({
                command: message,
                channel: 'upgrade'
            });
            console.log(`[ACK] 청크 ${chunkNumber} 재전송 완료`);
            
            // ACK 대기
            const ack = await this._waitForAck(chunkNumber, this.ackSettings.timeout);
            
            if (ack.success) {
                console.log(`[ACK] 청크 ${chunkNumber} 재전송 성공!`);
                return { success: true, retryCount };
            } else if (retryCount < this.ackSettings.maxRetries) {
                // 재귀적 재전송 시도
                return await this._retransmitChunk(message, chunkNumber, retryCount + 1);
            } else {
                // 최대 재시도 횟수 초과
                console.error(`[ACK] 청크 ${chunkNumber} 최대 재전송 실패 (${this.ackSettings.maxRetries}회 시도)`);
                return { 
                    success: false, 
                    retryCount, 
                    error: 'Max retries exceeded'
                };
            }
            
        } catch (error) {
            console.error(`[ACK] 청크 ${chunkNumber} 재전송 오류:`, error);
            return { 
                success: false, 
                retryCount, 
                error: error.message 
            };
        }
    }
}

// 전역에 클래스 노출
window.WebFirmwareUploader = WebFirmwareUploader;