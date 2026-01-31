# Changelog

## 간략 버전 정보 (Summary)

| Version | Date | Summary | Key changed files |
|---|---|---|---|
| **v1.3.7** | - | **카메라 스트리밍 비동기화**: 캡처는 스레드로 분리하고, BLE 전송은 메인 루프에서 청크 단위로 분산 처리하여 버저/센서 명령 응답성을 개선 | `source/lib/bleIoT.py`, `IoTmode/test/integratedBleLib_Camera.js`, `CHANGELOG.md`, `VERSION`, `source/config.py`, `README.md` |
| **v1.3.6** | - | **초기 공개 버전(기준선)**: EZMaker 센서/액츄에이터 + BLE 명령 + 웹(Web Bluetooth) 테스트/블록 연동 기반을 정리 | `source/lib/bleBaseIoT.py`, `source/lib/bleIoT.py`, `IoTmode/test/integratedBleLib_Camera.js`, `EZMaker_블록코드정의.md`, `EZMaker프로젝트.md` |

> Date는 릴리즈 노트에서 확정해 채워 넣을 수 있습니다.

---

## 상세 버전 히스토리 (Details)

### v1.3.7

#### 간략 변경 요약
- **카메라 스트리밍 구조 개선**: “캡처(스레드)” + “전송(메인 루프 펌프)”로 분리해 장시간 블로킹을 제거
- **버전 관리 체계 정리**: `VERSION`/`README.md`/`source/config.py(firmware_source)`를 `1.3.7`로 동기화

#### 상세 변경 내용
- **카메라 스트리밍(펌웨어)**
  - **캡처 스레드 도입**: 카메라 프레임 캡처를 `_camera_worker()` 스레드에서 수행하도록 변경
  - **전송 펌프 도입**: BLE notify 전송은 `_camera_tx_pump()`가 메인 루프에서 한 번에 제한된 청크만 전송하도록 변경
    - 기존 프로토콜(`CAM:START` → `SIZE:n` → `BIN{seq}:<chunk>`… → `CAM:END`)은 유지
    - 메인 루프의 “카메라 전송 루프 장시간 점유”를 줄여 **버저/센서 write 처리 지연을 완화**
  - **프레임 큐 폭주 방지**: `_cam_pending_frame`에 **최신 프레임 1개만 유지**(메모리 폭증 방지)
  - **스트리밍 종료 정리 강화**: `CAM:STREAM:OFF`/disconnect 시 전송 상태를 정리하여 호스트 파서가 중간 상태로 멈추지 않도록 처리

- **웹(Web Bluetooth) 테스트 라이브러리 성능/디버깅 개선** (`IoTmode/test/integratedBleLib_Camera.js`)
  - **로그 레벨(3단계) 도입**: `none / info / debug`
    - **`none`**: 로그 완전 비활성(카메라 스트리밍/대량 notify에서 성능 우선)
    - **`info`**: 프레임 단위 요약 중심(예: `SIZE`, 프레임 완료, 이미지 조립 완료)
    - **`debug`**: 청크 수신/알림 이벤트 등 고빈도 디버깅 로그 포함(성능 저하 가능)
    - 런타임 변경 예: `window.EZ_LOG.setLevel('debug'|'info'|'none')`
    - 초기값 지정 예: `window.EZ_LOG_LEVEL = 'debug'` (스크립트 로드 전에 세팅)
  - **고빈도 로그 억제**: 카메라 청크 수신/알림 이벤트 등 “프레임당 수십~수백 번” 발생할 수 있는 로그는 `debug`로만 출력되도록 분리
  - **console 라우팅(파일 내부)**: 파일 내 `console.log/warn/error`를 각각 `debug/info` 레벨로 라우팅하여,
    기존 코드의 로그 호출을 전부 수작업 치환하지 않아도 레벨 기반으로 일괄 제어 가능
  - **청크 크기 정합성 수정**: JS 카메라 파서의 `this.chunkSize`를 펌웨어(160B 청크)와 일치하도록 설정
    - 목적: `expectedChunks = ceil(size / chunkSize)` 계산/표시의 혼동 제거

---

### v1.3.6

#### 버전 특징(기준선)
- **프로젝트 통합 기반 확립**
  - DeepCoB(Esp32‑S3) + EZMAKER Shield 환경에서 **MicroPython 펌웨어(`source/`)** 와 **웹(Web Bluetooth) 테스트(`IoTmode/`)** 를 한 저장소에 통합
  - BLE 특성/명령 문자열 기반으로 센서·액츄에이터를 제어하는 구조 확립
- **블록/웹 연동 문서화**
  - 블록 사양을 `EZMaker_블록코드정의.md`로 정리(블록 문구 ↔ JS 템플릿 ↔ BLE 명령 흐름)
  - 프로젝트/핀맵/센서 목록을 `EZMaker프로젝트.md`로 정리

