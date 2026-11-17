# 真机验收报告（最终收口版）

- 日期：2026-11-17
- 设备：M5Stack Cardputer ADV / ESP32-S3 / Stamp-S3A
- 主机：Windows 10 Pro 22H2 Build 19045.6466
- 候选固件：`nucleos-0.8.7.0-msos20-winncm-r0101.bin`
- 候选大小：3,176,592 B
- 候选 SHA256：`05cf26580fc324e3c4985c27a61f876769add1d8b534b9bf42f1e71e6dbe6e6a`
- 写入槽：`ota_1 @ 0x3A0000`（依据 OTA 记录与候选独有 REV_0101 间接确认；启动日志未直接打印分区偏移）

## 总结

按最终验收口径（A–J 共 10 项）：**9 项 PASS、1 项 FAIL（I）、1 项子项 NOT_RUN（H 写入）**。
计数说明：A–F 六项全 PASS；G 的枚举 / COM 打开 / 日志读取三个子项均 PASS，故 G 计为 PASS；H 的只读部分 PASS、写入子项 NOT_RUN（单列，不并入通过数）；I 枚举 PASS 但输入 FAIL，故 I 计为 FAIL；J PASS。合计 9 PASS + 1 FAIL = 10 项，另有 1 个 NOT_RUN 子项。

| 项目 | 结果 | 证据摘要 |
|---|---|---|
| A — Compatible ID | PASS | CompatibleIds 首项 `USB\\MS_COMP_WINNCM`；Hardware ID 含 `REV_0101`；ProblemCode 0 |
| B — 驱动绑定 | PASS | `Service=UsbNcm`、`usbncm.inf`、Microsoft 10.0.19041.1、Class=Net |
| C — DHCP | PASS | NCM 网卡获得 `192.168.7.2/24`，来源 DHCP |
| D — 路由 | PASS | `192.168.7.0/24` 指向 NCM ifIndex 36；Meta Tunnel 不在该路由中 |
| E — HTTP | PASS | `curl --noproxy "*"` 返回 HTTP 200；本地地址 `192.168.7.2`；不存在的 `.99` 阴性对照超时 |
| F — PIN/Web | PASS | PIN 登录成功，进入 NucleoOS Web 桌面 |
| G — Serial/JTAG | PASS（枚举/COM/日志） | `VID_303A:PID_1001`；COM4；捕获 3,248 B / 43 行启动日志；无 panic/abort/watchdog |
| H — MSC | PASS（只读）/ NOT_RUN（写入） | `TinyUSB Flash Storage` 识别为 7.68 GB J: FAT32；目录可读；介质可写，因此未做写测试 |
| I — HID | FAIL（输入行为） | HID 键盘枚举成功、字符可达；松开 `c` 后持续重复输入 |
| J — 退出 USB-Web | PASS（UI/链路释放） | 返回主菜单；`303A:4006` 消失；NCM 适配器与 `192.168.7.x` 地址下线 |

## 关键网络证据

- Windows NCM 接口：`UsbNcm Host Device`，ifIndex 36。
- IPv4：`192.168.7.2/24`，DHCP 来源。
- 网关 / DHCP Server：`192.168.7.1`。
- 路由：`192.168.7.0/24 → ifIndex 36`。
- HTTP：`http://192.168.7.1` 返回 200，body 21,214 B。
- 假阳性阴性对照：访问不存在的 `192.168.7.99` 超时，HTTP 000，邻居 Unreachable；排除了 Meta Tunnel Fake-IP 假阳性。

## OTA 记录与启动证据

- `0x0F000`：`seq=1 / VALID`，原记录逐字节未变。
- `0x10000`：`seq=2 / VALID`，候选记录完成 `NEW → PENDING_VERIFY → VALID`。
- G 项串口日志捕获 3,248 B / 43 行，启动链到达 `pre-app-run`，65.40 秒进入屏保。
- 日志未直接记录 `Loaded app from partition at offset`，因此启动分区偏移标记为**不可直接观察**。候选身份由运行时 `REV_0101`（本候选独有）与 OTA 记录共同间接支持。

## 已知问题与范围边界

### HID 连发

USB HID 设备枚举成功，按键字符可以到达 Windows，但释放 `c` 后仍持续重复。没有对官方原版固件进行 A/B 对照，因此不判断这是上游原有缺陷还是其他因素造成；本项目不修复 HID。

### 启动内存告警

串口启动日志出现一次：
`oom: alloc fail: 32404 B caps=0x8 in heap_caps_malloc`

随后 UI 自动降级到 `240x130` 画布并继续运行；未观察到 panic、abort 或 watchdog。该项记录为受控降级，不属于本次 NCM 修复范围。

### 未执行的测试

- MSC 写入测试：未执行，避免对用户 SD 卡产生写入。
- 精确启动分区偏移：日志中不可观察，不推断。

## 操作边界

验收期间未修改 Windows 驱动、INF、注册表或签名策略；未格式化或写入 SD 卡；未清空 otadata；未覆盖原活动 OTA 槽；未使用完整合并镜像写入 OTA 槽。
