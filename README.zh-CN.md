# NucleoOS Windows 10 USB NCM 兼容性修复

> 面向 **M5Stack Cardputer ADV** + **NucleoOS v0.8.7** 的独立兼容性研究与修复记录。

**当前状态：已在一台真实 Windows 10 主机上完成核心功能验证。精确源码补丁与哈希已核验的工具已收录；本仓库不分发固件二进制，也不复制上游源码。**

本项目记录了一次真实的 Windows 10 USB CDC-NCM 枚举问题、采用 Microsoft OS 2.0 / `WINNCM` 描述符的修复路线，以及设备端和主机端的实测结果。

## 结果

在本次测试的 Cardputer ADV + Windows 10 环境中，修复版固件向 Windows 暴露了 `USB\MS_COMP_WINNCM`。Windows 自动绑定系统自带的 `UsbNcm` 驱动，通过 DHCP 获取地址，经 NCM 接口访问设备，并成功打开 NucleoOS Web 桌面。

本次验收没有安装第三方 Windows 驱动，也没有修改 Windows INF、注册表、驱动签名策略或网络栈配置。

### 已验证的通信链路

1. USB Compatible ID 出现 `USB\MS_COMP_WINNCM`。
2. Windows 自动绑定 Microsoft `usbncm.inf`（服务 `UsbNcm`）。
3. Windows 通过 DHCP 获得 `192.168.7.2/24`。
4. `192.168.7.0/24` 路由指向 NCM 网卡，而不是 Meta Tunnel。
5. `http://192.168.7.1` 经 NCM 接口返回 HTTP 200。
6. PIN 配对成功，进入 NucleoOS Web 桌面。

完整证据见 [真机验收报告](docs/ACCEPTANCE.md)。

## 本项目范围

本仓库只处理 Windows 10 CDC-NCM 兼容性：

- Microsoft OS 2.0 / `WINNCM` 描述符集成。
- `bcdUSB = 0x0210`、NCM 模式 `bcdDevice = 0x0101`。
- 锁定经过测试的 ESP-IDF / TinyUSB 依赖基线。
- OTA 安全部署说明与真机验收证据。

不宣称修复 NucleoOS 的其他功能。USB HID 键盘测试中，设备可以枚举并输入字符，但观察到松键后字符持续重复的问题。没有用官方固件做 A/B 对照，因此不将其归因于本次 NCM 补丁；该问题明确排除在本项目范围之外。

## 验收摘要

| 项目 | 结果 |
|---|---|
| Windows 10 NCM 枚举及 `WINNCM` | PASS |
| 系统自带 `UsbNcm` 驱动绑定 | PASS |
| DHCP 与 NCM 路由 | PASS |
| HTTP 与 PIN 配对 | PASS |
| USB Serial/JTAG 枚举及启动日志 | PASS |
| USB MSC 目录读取 | PASS |
| USB MSC 写入测试 | NOT RUN（介质可写，但没有执行写入） |
| USB HID 输入 | FAIL（松开 `c` 后持续连发）；不属于 NCM 修复范围 |
| 退出 USB-Web 后返回正常系统 | PASS（设备/UI 侧） |
| 串口日志直接确认启动分区偏移 | 未观察到；候选身份由 `REV_0101` 与 OTA 记录间接支持 |

完整矩阵见 [docs/ACCEPTANCE.md](docs/ACCEPTANCE.md)。

## 仓库结构

- `docs/`：根因、实现说明、验收、OTA 部署、构建与恢复指南。
- `patches/full-diff-complete.patch`：本次修复的精确 diff，直接从本地工作树导出（`8a5c6be..a51c571`，4 个文件，+337/−3）。
- `tools/`：两个 OTA 记录处理工具，SHA256 均已与工程记录逐位核对。
- `tests/descriptor-tests/`：描述符校验结果（66 项：7 设备描述符 + 41 MS OS 2.0 + 18 配置描述符）及产出这些结果的校验脚本。
- `evidence/`：脱敏后的串口启动日志与采集元数据。
- `SHA256SUMS`：覆盖本仓库全部文件的完整性清单。

固件二进制与上游源码副本不在本仓库分发，详见 [许可证与署名说明](docs/LICENSE-AND-ATTRIBUTION.md)。

## 测试环境

- 设备：M5Stack Cardputer ADV / ESP32-S3 / Stamp-S3A
- 固件基线：NucleoOS v0.8.7
- 候选修订：`bcdUSB 0x0210`、`bcdDevice 0x0101`
- VID/PID：`303A:4006`
- ESP-IDF：5.4.4
- `esp_tinyusb`：1.7.6~2
- TinyUSB：0.19.0~3
- 主机：Windows 10 Pro 22H2，Build 19045.6466

结果来自一台真实设备和一台 Windows 主机，不能外推为所有 Windows 版本、Cardputer 型号或其他操作系统均兼容。

## 上游项目

- NucleoOS：https://github.com/indecenti/NucleoOs
- 测试基线：`v0.8.7`
- TinyUSB：https://github.com/hathach/tinyusb
- Microsoft USB 设备类驱动文档：https://learn.microsoft.com/en-us/windows-hardware/drivers/usbcon/supported-usb-classes

本项目是独立社区工作，与 M5Stack、NucleoOS 维护者、Microsoft、Espressif、TinyUSB 均无隶属或背书关系。

## 许可证与再分发

NucleoOS v0.8.7 声明使用 **PolyForm Noncommercial License 1.0.0**。不要默认认为上游源码、衍生补丁或固件二进制可以重新标记为 MIT、Apache 或 GPL。公开衍生源码或二进制前，必须核对上游许可证及其要求的声明。

本仓库不包含 NucleoOS 固件二进制，也不复制上游源码。原创文档与工具的许可证口径见 [许可证与署名说明](docs/LICENSE-AND-ATTRIBUTION.md)。

## 发布状态

本仓库发布的是文档、证据、精确源码补丁与已核验的主机侧工具，**不是固件发行版**：不含任何二进制，也不复制上游源码树。

打 `v1.0.0` Tag 前仍需：

1. 用干净的 NucleoOS v0.8.7 检出应用本补丁重新构建，复核记录中的描述符结果。
2. 确认衍生补丁的许可证口径（见 [许可证与署名说明](docs/LICENSE-AND-ATTRIBUTION.md)）。
3. 再次检查未引入私人标识或本机绝对路径。
4. 决定 HID 连发现象是否值得上游报告——它不属于本项目范围。
