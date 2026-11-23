<p align="center"><img src="docs/assets/sony-cloud-logo.png" width="112" height="112" alt="索尼云创 · Sony Imaging Cloud"></p>

# 索尼云创 · A7C II Tools

[English](README.md) · **简体中文**

适用于 **Sony A7C II（ILCE-7CM2）** 的桌面工具：生成卡刷固件，配置 FL2／FL3、自定义创意外观、机械／电子快门声音和竖屏显示。

[下载最新版](https://github.com/QAQLeonard/a7c2-tools/releases/latest) · [更新日志](docs/zh-CN/changelog.md) · [索尼云创](https://sony.leonardsaikou.top)

> [!WARNING]
>
> ### 使用前必读 · 免责声明
>
> **本工具属于非官方独立研究，仅供学习与技术交流，与索尼无隶属、授权或背书关系。**
>
> ### 重要：可能变砖，且不保证救回
>
> **修改相机可能导致无法开机、反复重启、拍摄或回放时崩溃、功能异常或数据丢失，也可能影响官方更新、保修或维修，甚至需要付费维修或更换主板。**
>
> **写入成功、完整读回及离线测试通过，都不代表启动安全或所有模式稳定。名称、图标等显示资源修改同样存在风险；部分功能组合尚未全部完成实机验收。**
>
> **一键恢复不是完整系统重装，不保证能救回相机；备份、相机初始化或官方升级也不保证能够恢复。出现错误、断连或结果不明时，请停止写入、保留诊断，不要反复点击安装或恢复。**
>
> ### 禁止一切商用牟利行为
>
> **禁止一切商用牟利行为。本人明确反对收费代刷、远程收费安装、倒卖或打包售卖工具、付费解锁、制作或售卖激活码／加密狗，以及捆绑硬件牟利等行为。本项目免费提供，作者不提供有偿代刷，也未授权任何人以作者名义开展上述收费业务。**
>
> ### 严禁冒充官方或作者授权
>
> **作者从未授权任何人以作者或索尼官方名义开展收费服务、宣传或承诺保修。严禁冒充索尼官方、作者本人或授权服务商；第三方收费不代表作者参与、认可、背书或担保。**
>
> **仅操作本人合法持有或已获机主明确授权的设备；请妥善备份重要数据。如无法承担设备损坏与维修风险，请退出。**
>
> **本发行版的项目原创代码采用 [PolyForm Noncommercial License 1.0.0](LICENSE)。具体适用范围及第三方权利见[来源与许可](docs/zh-CN/notices.md)；本声明不排除法律禁止免除的责任。**
>
> **[点击阅读完整《风险告知与使用声明》](docs/zh-CN/notices.md#风险告知与使用声明)**

## 支持的机型

> [!IMPORTANT]
> **本工具只支持 Sony A7C II（ILCE-7CM2），固件 2.01。**其他机型（包括初代 A7C、A7 IV、A7CR、A7R V、A6700、A7 V 等）都**不能**使用，程序会拒绝连接，请不要尝试。

下表汇总相关机型的独立项目和研究资料。各项目的支持范围、使用方式和风险请以其自身说明为准。

| 机型 | 项目 | 内容 |
| --- | --- | --- |
| **A7R V** | [Michael（Hearts-Ace）／sony-a7r5-custom-firmware](https://github.com/Hearts-Ace/sony-a7r5-custom-firmware) | 自定义固件、FL2／FL3、创意外观与声音资源，以及 RAW 色彩研究；本项目色彩拟合与算子实现的重要来源。 |
| **A7 IV** | [Erlla/sony-a7m4-custom-firmware](https://github.com/Erlla/sony-a7m4-custom-firmware)<br>[happyfrog2026/a7m4-color-research](https://github.com/happyfrog2026/a7m4-color-research)<br>[happyfrog2026/a74-recovery-tools](https://github.com/happyfrog2026/a74-recovery-tools)<br>[Itinerary200/a7m4-lut](https://github.com/Itinerary200/a7m4-lut)<br>[DavidBuchanan314/ILCE-7M4-RE](https://github.com/DavidBuchanan314/ILCE-7M4-RE) | 固件定制与卡刷；色彩管线、自定义外观、名称／图标和电子快门声音；备份恢复工具；多色彩空间 LUT 转换；底层逆向与 Fastboot。 |
| **A7CR** | [lzh2016zzz/a7cr-fl23-research](https://github.com/lzh2016zzz/a7cr-fl23-research)<br>[injectiver/a7cr-creative-look-tools](https://github.com/injectiver/a7cr-creative-look-tools) | FL2／FL3 移植研究；原生与自定义外观、macOS USB 和 RAW／JPEG 诊断研究工具。 |
| **A7C II** | [SONY-FW/a7c2-re](https://github.com/SONY-FW/a7c2-re)<br>[chocotan/a7c2-qemu](https://github.com/chocotan/a7c2-qemu)<br>[MDHan/a7c2-fl23-macos](https://github.com/MDHan/a7c2-fl23-macos)<br>[YuuLuo/a7c2-service-preload](https://github.com/YuuLuo/a7c2-service-preload) | 固件逆向、启动链与更新器研究；独立 QEMU 模拟器；FL2／FL3 的 macOS 适配；USB 服务认证及临时执行研究。 |
| **A6700** | [xyzhangxin/sony-a6700-powerful](https://github.com/xyzhangxin/sony-a6700-powerful) | Powerful6700 功能工具、自定义快门声音、USB 维护协议及 Pico／Fastboot 备份研究。 |
| **A7 V** | [751K/sony-a7m5-looks · Sony Look Bridge](https://github.com/751K/sony-a7m5-looks) | 照片显影与创意外观的后期配置文件、S-Log3 视频 LUT、DCTL 及 ARW 解码研究，涵盖多款索尼机型。 |

**交流群：**[Telegram（推荐）](https://t.me/sonyfwlab) · [Discord](https://discord.gg/SwPdfSd9c)
**作者：**小红书 [QAQLeonard（读研版）](https://www.xiaohongshu.com/user/profile/660501f7000000000600d03c) · 抖音 **LeonardZ**（抖音号 `90860261487`）

> [!IMPORTANT]
> 本工具会修改相机固件中的程序和设置。请先完整读一遍下面的[操作指南](#操作指南)再动手。遇到软件报错时，**先导出诊断包，不要反复重试写入**。

正常打开应用时须阅读风险摘要，手动勾选接受后才能进入；可点击[《风险告知与使用声明》](docs/zh-CN/notices.md#风险告知与使用声明)查看全文。工具免费提供、与索尼无官方关系；作者反对收费代刷，禁止冒充官方或作者授权。项目原创代码采用标准 PolyForm Noncommercial License 1.0.0，第三方及旧版许可分别保留。

**固件来源：**生成安装或恢复固件需要自行从索尼取得官方 **ILCE-7CM2 2.01 `BODYDATA.DAT`**；安装包不附带完整官方固件或原厂语音包。首次授信自动保留本机原厂公钥的恢复记录，请妥善保存。

## 目录

- [支持的机型](#支持的机型)
- [能做什么](#能做什么)
- [下载与系统要求](#下载与系统要求)
- [开始前必读](#开始前必读)
- [操作指南](#操作指南)
  - [第 1 步：安装驱动（Windows）](#第-1-步安装驱动windows)
  - [驱动出错：先卸载再重装](#驱动出错先卸载再重装)
  - [驱动还是装不上：用 Zadig 手动安装](#驱动还是装不上用-zadig-手动安装)
  - [第 2 步：生成固件](#第-2-步生成固件)
  - [第 3 步：首次授信与刷前配置](#第-3-步首次授信与刷前配置)
  - [第 4 步：卡刷与检查](#第-4-步卡刷与检查)
- [单独使用各功能](#单独使用各功能)
- [常见问题](#常见问题)
- [验证状态](#验证状态)
- [命令行与开发](#命令行与开发)
- [更新记录](#更新记录)
- [来源与许可](#来源与许可)
- [滤镜效果对比](#滤镜效果对比)
- [致谢](#致谢)
- [赞助](#赞助)

## 能做什么

| 功能 | 说明 |
| --- | --- |
| **安装向导** | 准备驱动、生成固件、首次授信、写入配置，再手动卡刷；Mac 省去驱动步骤。 |
| **FL2／FL3** | 生成固件时选择是否加入这两款创意外观。 |
| **自定义创意外观** | 把 `.a7look` 写入自订 1–6 并设置机内名称，或把槽位恢复为 ST；没列出的槽位不受影响。 |
| **外观转换** | 从 DCP 或 CUBE 离线输出配套的 `.a7look` 和 `.dcp`，不需要 Lightroom；安装包内置六款带图标 A7Look，其他外观与 DCP 从索尼云创获取。 |
| **Lightroom 插件** | 导入 RAW 时，按拍摄时用的自订槽位自动套用对应的 DCP。 |
| **快门声音** | 分别开启／关闭机械、电子快门的扬声器音效；自定义音频可选只修改机械、只修改电子或两者。 |
| **竖屏显示** | 竖握相机时，拍摄信息和图标跟着转向（整个 MENU 不转）。 |
| **恢复原厂功能** | 使用官方固件生成恢复 DAT，准备升级识别版本后手动卡刷。 |

## 下载与系统要求

| 系统 | 下载 | 说明 |
| --- | --- | --- |
| **Windows 10／11 x64** | [Releases](https://github.com/QAQLeonard/a7c2-tools/releases) 中的 `A7C2Tools-Windows-x64.zip` | 整包解压后运行 `A7C2Tools.exe`。`_internal` 和 `Profiles` 文件夹要和它放在一起，不要单独拷出 EXE。不需要另装 Python。 |
| **macOS 14+（Apple Silicon）** | [Releases](https://github.com/QAQLeonard/a7c2-tools/releases) 中的 `A7C2Tools-macOS-arm64.dmg` | 把 APP 拖进“应用程序”再打开。没有开发者签名，首次打开需在“系统设置 → 隐私与安全性”中允许。不提供 Intel 版。**Mac 实机 USB 尚未验证。** |

安装包内置六款带图标的 `.a7look`，用于写入相机。其他外观和用于 Lightroom RAW 显影的 `.dcp` 可从[索尼云创](https://sony.leonardsaikou.top)获取。

Windows 固件生成使用包内工具，无需另装 WSL、Ubuntu 或 Python。Mac 也无需另装 Python 或 Homebrew。

相机：**ILCE-7CM2，固件 2.01**。其他机型和固件版本一律不支持。

## 开始前必读

- **电量：**电池至少 50%。每次写入前，软件都会弹窗请你确认供电。
- **连接：**用能传数据的 USB 线直接插在电脑上，尽量不经过扩展坞或 Hub。一次只连一台相机。
- **USB 模式：**相机菜单里把 USB 连接设为 **海量存储（Mass Storage）**。
- **正常现象：**连接或切换驱动时，相机显示 **“请检查所连接的设备”**，电脑也可能不显示相机盘符，这些都是正常的。成功与否以软件里的进度和日志为准，不要因为这条提示拔线或重装驱动。
- **写入时：**软件显示正在执行时，不要拔线、关机或关闭软件。只有软件明确提示“读写已结束”后，才按提示操作。
- **打开软件本身**不会连接或写入相机。

> [!NOTE]
> **保存外观或声音后**，按软件提示断电重开以加载新内容，步骤是：
>
> 1. 拔掉 USB 线和其他外部供电。
> 2. 等存取灯停止闪烁。
> 3. 把电源拨到 OFF，等屏幕和存取灯完全熄灭。
> 4. 取下电池，**至少等 1 分钟**。
> 5. 装回电池，开机。
>
> 只关机再开机不算断电重开。**刷前写入配置是例外：写完后保持开机直接卡刷；中途重启须重新写配置。**

## 操作指南

按软件默认的“安装向导”操作：**准备驱动 → 生成固件 → 首次授信 → 写入配置并卡刷**。Mac 从生成固件开始。

### 第 1 步：安装驱动（Windows）

软件和相机之间要经过两种 USB 身份通信：普通的海量存储 `054C:0E8A`，以及认证后的服务连接 `054C:0336`。这两种身份都需要 WinUSB 驱动。

1. 相机开机，选择海量存储，连接电脑。
2. 打开软件左侧的 **高级设置**。
3. 点 **检测相机与驱动**。日志里应能看到 `054C:0E8A`。如果看不到，检查数据线和 USB 模式。
4. 点 **准备两阶段驱动并测试连接**：
   - 软件先准备管理员权限和安装器、处理 `0E8A`，再让相机进入服务连接；通过 Windows PnP 捕获 `0336` 后自动处理第二阶段驱动。
   - Windows 会在切换模式前请求所需的管理员权限，点“是”。驱动安装耗时不占接口重新枚举的等待窗口，无需到设备管理器抢时间更新。
   - 已经装好可用驱动（WinUSB／libusbK／libusb0）的身份会直接沿用，不重复安装。
   - 过程中相机显示“请检查所连接的设备”是正常的。
5. 日志出现 **“服务连接成功，驱动准备结束”** 就完成了。这一步**不会写入相机固件**。
6. **推荐：**在第一次写入之前，点 **检测 USB 连接稳定性（只读）** 测一下数据线和接口。
   - 测试**至少持续 2 分钟**，反复读取相机里的两个程序文件（写入后完整读回的也是这两个文件），每一轮都和第一轮逐字节比对。
   - 任何一次读取出错、内容不一致，或单次读取超过 20 秒，都判为不通过。
   - 全程只读，不写入相机。
   - 写入或读回时如果掉线，结果可能变成“未知”，处理起来很麻烦。所以写入前先确认连接稳定。
   - 没通过就换一根线，或换电脑后侧的 USB 口，直到测试通过再继续。
   - 测试通过不代表写入期间一定不会掉线。写入时仍要保持线和供电稳定。

> [!TIP]
> 一键安装开头也会自动检查并准备驱动。单独先做这一步的好处是：驱动问题能在写入任何东西之前就暴露出来。

**macOS：**不需要安装驱动。
- 先关闭“照片”“图像捕捉”等可能占用相机存储卡的程序。
- 在 **高级设置** 页点 **准备 USB 服务连接**。
- 每次相机操作都会打开一个“终端”窗口，请在里面输入 **Mac 登录密码**，用来通过 sudo 接管 USB。程序不读取也不保存密码；输入前关掉窗口，相机操作就不会开始。

### 驱动出错：先卸载再重装

出现以下任一情况，说明驱动状态可能不对：
- 第 1 步报错，或者提示 `0336` 出现了但接口打不开。
- 以前用 Zadig 等工具装过别的驱动。
- 相机连上后 Windows 一直识别异常。

这时**先卸载，再按第 1 步重装**：

1. 在 **高级设置** 页点 **卸载相机驱动，恢复 Windows 默认连接**，确认，并在 Windows 弹窗中允许管理员权限。
   - 只处理 Sony `054C:0E8A`／`054C:0336` 的第三方驱动，不影响其他设备，也不修改相机固件。
   - 卸载前会把驱动包备份到任务目录。
2. 按日志提示操作：
   - 一般是**拔掉 USB，再以海量存储模式重新插上**，让 Windows 换回默认驱动。
   - 如果日志提示 Windows 需要重启，就重启电脑（软件不会自动重启）。
3. 回到[第 1 步](#第-1-步安装驱动windows)，重新点 **准备两阶段驱动并测试连接**。

还是不行的话，换一根线、换一个电脑后侧的 USB 口，用 **检测 USB 连接稳定性（只读）** 排查。仍不行就点窗口底部的 **导出诊断包**，发到交流群。

### 驱动还是装不上：用 Zadig 手动安装

软件自动装驱动失败的电脑，大多数改用 [Zadig](https://zadig.akeo.ie/) 手动安装就能成功。整个过程不写入相机，只更换这台电脑上相机两个 USB 身份所用的驱动。

软件 **高级设置** 页上，**准备两阶段驱动并测试连接（自动）** 旁边就是 **用 Zadig 手动安装驱动（自动失败时）** 按钮，点开有下面同样的步骤和 Zadig 下载链接。

**先了解：相机有两个 USB 身份，两个都要装驱动**

| 阶段 | Zadig 里显示的名称 | USB ID | 什么时候出现 |
| --- | --- | --- | --- |
| 普通连接 | `ILCE-7CM2` | `054C` `0E8A` | 相机开机、选海量存储、接上电脑 |
| 服务模式 | `Sony USB Device` | `054C` `0336` | 软件认证之后才出现，相机屏幕通常显示“请检查所连接的设备” |

**准备**

1. 从 Zadig 官网下载最新版 `zadig-x.x.exe`（单个文件，不用安装）。
2. 完全关闭本软件。
3. 相机开机，菜单里的 USB 连接选 **海量存储（Mass Storage）**。用能传数据的线直接接电脑：不要经过扩展坞，台式机用机箱后面的口。

**第一部分：给 `0E8A` 装驱动**

1. 右键 Zadig，选 **以管理员身份运行**。弹出是否检查更新的提示时，选哪个都可以。
2. 在菜单 **Options** 里勾选 **List All Devices**。不勾选就看不到相机。
3. 在上方下拉框里选 **`ILCE-7CM2`**。
4. **核对 USB ID 一栏是 `054C` `0E8A`。** 对不上就是选错了，换一项再核对。不要给键盘、鼠标、U 盘、网卡等其他设备换驱动。
5. 绿色箭头左边是当前驱动（例如 `USBSTOR`）。在箭头右边的驱动框里，用上下箭头选 **libusbK**。
6. 点大按钮 **Replace Driver**（当前没有驱动时显示为 **Install Driver**）。等 1–2 分钟，直到提示 **The driver was installed successfully**。
7. 换好后，电脑上相机的盘符会消失，相机显示“请检查所连接的设备”。这都是正常的。
8. 等安装结束，关闭 Zadig；拔 USB、相机关机并等灯灭、取下电池至少 1 分钟，再装回开机、选择海量存储并重新连接。

**第二部分：让 `0336` 出现，再给它装驱动**

1. 关闭 Zadig。在本软件 **安装驱动** 页点 **准备两阶段驱动并测试连接**，不要让两个安装器同时运行。
2. 软件会沿用刚装好的 `0E8A` 驱动进行认证。认证后，相机变成 `Sony USB Device`（`054C 0336`）。
   - 软件自动给 `0336` 装好驱动、日志出现 **“服务连接成功，驱动准备结束”**：已经完成，直接看第三部分。
   - 软件提前准备安装器，`0336` 出现后自动安装并重新等待接口，**不需要抢时间点 Install**。
3. 自动任务失败并已停止后，若 `0336` 仍在，才打开 Zadig，勾选 **Options → List All Devices**，选 **Sony USB Device**，核对 USB ID 为 **054C 0336**，再安装 **libusbK**。
4. 若 `0336` 已消失，不要反复认证或让两个安装器抢装；保留日志核对消失阶段。设备消失不等于已经恢复为 `0E8A`。

**第三部分：断电后重新测试**

1. 拔掉 USB，相机关机，**取出电池约 1 分钟**。装回电池开机，选海量存储，重新接上。
2. 在本软件里再点一次 **准备两阶段驱动并测试连接**。日志出现 **“服务连接成功，驱动准备结束”** 后，就可以进行[第 3 步：首次授信与刷前配置](#第-3-步首次授信与刷前配置)。

**检查是否装对：** 打开 Windows 设备管理器，应能看到 **libusbK USB Devices** 分类，下面有 `ILCE-7CM2`；装过 `0336` 后还会有 `Sony USB Device`。

**遇到问题**

- **libusbK 安装失败：** 重新以管理员身份运行 Zadig 再试。仍然失败，可以改选 **WinUSB**。本软件可以使用 WinUSB、libusbK、libusb0 中的任意一种。
- **下拉框里没有相机：** 确认 **List All Devices** 已勾选，相机已开机、选了海量存储，并换一根能传数据的线。
- **恢复电脑驱动：** 在 **安装驱动** 页点 **卸载相机驱动，恢复 Windows 默认连接**；匹配相机的第三方驱动先备份再移除。若机身仍报告 `0336`，不能保证只靠卸载电脑驱动就恢复为 `0E8A`。
- **Mac 不需要装驱动。**

### 第 2 步：生成固件

1. 在“生成固件”选择自行取得的官方 **ILCE-7CM2 2.01 `BODYDATA.DAT`**。
2. 选择 FL2／FL3、外观、声音、竖屏显示等功能。外观可使用默认六款或自选 `.a7look`；声音可用默认素材或自己的音频。
3. 选择保存位置，可直接选择 SD 卡根目录。成功后得到 `BODYDATA.DAT`；同名构建文件会覆盖，目录内无关文件保留。
4. 将存有该文件的 SD 卡安全弹出并装入相机，继续下面的授信和配置。

### 第 3 步：首次授信与刷前配置

1. 正常开机，以 USB 海量存储模式连接电脑。
2. 第一次使用时，在“首次授信”安装机身公钥；已经授信的机身可跳过。保留软件自动保存的首次授信恢复记录。
3. 通过 USB **写入本次功能配置**，等待软件明确提示读写结束。
4. **拔掉 USB，保持相机开机，直接在相机菜单执行固件更新。**卡刷前不要关机或取电池；中途重启过，请重新写配置。

### 第 4 步：卡刷与检查

按机身提示完成更新，过程中保持供电。正常开机后，检查所选功能：自订槽位的颜色、名称和图标，FL2／FL3、所选快门声音，以及竖握时拍摄信息转向。快门音效还受机内“音频信号”设置影响。

默认六款外观：

| 槽位 | 1 | 2 | 3 | 4 | 5 | 6 |
| --- | --- | --- | --- | --- | --- | --- |
| 外观 | Classic Negative（NC） | Classic Chrome（CC） | Nostalgic Negative（NN） | Astia（AS） | Ricoh Positive Film（RP） | Ricoh Negative Film（RN） |

## 单独使用各功能

### FL2／FL3

在“生成固件”选择是否加入 FL2／FL3，再按安装向导写入配置并卡刷。

### 自定义创意外观

在外观页选择目标槽位、`.a7look` 和机内名称，再应用更改；没有选择的槽位保留。支持带图标的完整 A7Look /2。保存完成后按软件提示断电重开，检查颜色、名称和图标。

在转换工具中，可从 DCP 或 CUBE 生成 A7Look 和 DCP。CUBE 要按其实际约定选择输入与输出空间，支持 S-Log3、V-Log 等；详见 [LUT 格式与色彩空间](docs/zh-CN/lut-formats.md)。Lightroom 插件按拍摄槽位匹配已登记的 DCP，不修改 RAW 数据。

### 快门声音

1. **机械／电子快门音效分别开启、关闭**：只控制扬声器声音，保留另一种的开关和已保存声音，不切换快门类型。机械结构本身仍会发声。
2. 选择音频或视频文件，设置 **起点** 和 **长度**（0.01–2 秒），点 **转换所选片段**。这一步只在电脑上处理，不连接相机。
3. 可选：用 **音量降低 −3 dB／音量提高 +3 dB／还原转换时音量** 调整音量。
4. 在统一自定义入口选择 **只修改机械／只修改电子／机械和电子都修改**，点 **保存到所选快门**。保存会开启所选音效，保留未选一侧的开关及声音；写入后按提示断电重开。
5. **相机内临时试听** 是可选步骤，使用电子快门：保持相机开机拔掉 USB，试拍后接回再保存。机械自定义音频在开启段播放，关闭段静音，避免重复播放同一片段。
6. **移除全部自定义音效，关闭电子快门音效** 会撤销两侧自定义声音；机械音效开关保留。相机全局“音频信号”关闭时仍可能抑制声音，本工具不自动修改它。

### 竖屏显示

在生成固件时勾选竖屏显示资源，并在刷前配置中启用。竖握相机时拍摄信息和图标转向，整个 MENU 不旋转；不增加机内竖屏开关菜单。

### 恢复原厂功能

1. 在“一键恢复”用官方 **2.01 `BODYDATA.DAT`** 生成原厂内容恢复包，正文和版本头均为 **2.01**。
2. 通过 USB 或已配置的 SSH 将升级识别版本设为 **2.00**。这一步只准备版本资料，不表示已经恢复固件。
3. 读写结束后按软件提示操作，将恢复 `BODYDATA.DAT` 放在卡根目录，在相机菜单手动更新。

如果要直接刷索尼原签名固件，还需在“首次授信”或“高级设置”恢复本机原厂公钥；仅修改版本号不会恢复授信。

## 常见问题

| 现象 | 处理 |
| --- | --- |
| 相机显示“请检查所连接的设备” | 正常现象。看软件日志判断进度。 |
| 未找到 `054C:0E8A` | 相机没选海量存储，或线不能传数据。改好后重新插线。 |
| `0336` 一直不出现 | 软件会冷却后自动重试，最多 3 次。仍失败就按[驱动出错](#驱动出错先卸载再重装)处理，或[用 Zadig 手动安装](#驱动还是装不上用-zadig-手动安装)。 |
| 认证后相机跳到回放画面，`0336` 一直不出现 | 换电脑上的 USB 2.0 口（或用 USB 2.0 数据线／扩展坞）再试；部分电脑走 USB 3 高速连接时相机不进服务模式。 |
| `0336` 出现了但接口打不开 | 驱动问题。卸载驱动后重装，不要反复点安装。 |
| 安装或恢复中途断了 | **先停止操作并导出诊断包。**只有软件明确显示等待重开／继续核对时，才按该阶段提示继续；结果不明时不要重新开始安装或恢复。已确认完成的程序写入不会重放。 |
| 软件提示“结果未知”或“需要核对” | **不要重试写入。**点 **导出诊断包**，发到交流群。 |
| 听不到快门声 | 检查机内“音频信号”是否开启。 |
| 外观颜色和 DCP 不完全一样 | 机内色表是拟合近似，属于正常范围。 |
| Mac 上终端要求输入密码 | 输入 Mac 登录密码，用于 sudo 接管 USB。 |

诊断包包含设备信息和本机路径，公开分享前请先检查。软件不会导出固件、机身校准或照片。

## 验证状态

各版本的实机覆盖、模型结果和未验收范围见[更新日志](docs/zh-CN/changelog.md)。离线测试或文件读回不等于所有拍摄模式及机身都已通过验证。

## 命令行与开发

图形界面已经覆盖日常使用。原有的命令行工具仍保留，供高级用户和开发使用：

| 入口 | 用途 |
| --- | --- |
| `python desktop.py` | 从源码运行桌面程序（64 位 Python 3.11，先 `pip install -r desktop-requirements.txt`） |
| `FL23.cmd` | 旧版 FL2／FL3 命令行安装 |
| `python lut.py` | 旧版外观导入与单槽恢复 |
| `python recovery.py` | 用原始备份完整回退 |
| `python a7look_compile.py` | 离线把 DCP／CUBE 编译成 `.a7look` |

离线测试（不访问相机）：`python -m pytest dev/desktop -q`。架构、构建和打包见 [开发说明](docs/zh-CN/development.md)。让 AI 修改代码前，请先读 [AGENTS.md](AGENTS.md)。

## 更新记录

版本变化见[更新日志](docs/zh-CN/changelog.md)，历史发布说明见 [Releases](https://github.com/QAQLeonard/a7c2-tools/releases)。安装包仅在[最新版](https://github.com/QAQLeonard/a7c2-tools/releases/latest)提供。

## 来源与许可

本发行版的项目原创代码采用标准 [PolyForm Noncommercial License 1.0.0](LICENSE)，禁止一切商用牟利行为；采用公开原文，不附加自拟许可证条款。旧版及第三方原有许可保留，见[旧版 MIT 文本](docs/licenses/project-legacy-MIT.txt)。DCP、参考外观和打包的第三方组件保留各自的许可与署名，见[许可说明](docs/zh-CN/notices.md)。富士 DCP 参考来自小红书 **门萨特里顿**，理光 DCP 参考来自小红书 **爸总林先森**。

本项目为独立研究，与 Sony、Fujifilm、Ricoh、Adobe 无关。外观名称不代表官方认可或颜色完全一致，本工具也不是索尼签名的更新。

## 滤镜效果对比

<details>
<summary>展开逐场景对比图</summary>

相机直出 JPG，仅缩放、拼接和添加标签；没有曝光、白平衡或色彩调整。拍摄参数存在变化，供效果参考，不是受控测量。

每组依次展示三张独立对比图：**ST／FL／FL2／FL3**、**ST／NC／CC／NN**、**ST／E／GR 正片／GR 负片**；每张四宫格按左上、右上、左下、右下读取。NC＝Classic Neg.，CC＝Classic Chrome，NN＝Nostalgic Neg.，E＝Eterna；这批不包含 Astia。

以下为历史版本拍摄样例；当前外观已重新拟合，图片仅供历史效果参考。

**01 · 饮料柜**

![01 · 饮料柜 — ST / FL / FL2 / FL3](docs/images/film-comparison/01_饮料柜/01-1_ST_FL_FL2_FL3.jpg)

![01 · 饮料柜 — ST / NC / CC / NN](docs/images/film-comparison/01_饮料柜/01-2_ST_NC_CC_NN.jpg)

![01 · 饮料柜 — ST / Eterna / GR Positive / GR Negative](docs/images/film-comparison/01_饮料柜/01-3_ST_E_GR正片_GR负片.jpg)

**02 · 绿植**

![02 · 绿植 — ST / FL / FL2 / FL3](docs/images/film-comparison/02_绿植/02-1_ST_FL_FL2_FL3.jpg)

![02 · 绿植 — ST / NC / CC / NN](docs/images/film-comparison/02_绿植/02-2_ST_NC_CC_NN.jpg)

![02 · 绿植 — ST / Eterna / GR Positive / GR Negative](docs/images/film-comparison/02_绿植/02-3_ST_E_GR正片_GR负片.jpg)

**03 · 柜台**

![03 · 柜台 — ST / FL / FL2 / FL3](docs/images/film-comparison/03_柜台/03-1_ST_FL_FL2_FL3.jpg)

![03 · 柜台 — ST / NC / CC / NN](docs/images/film-comparison/03_柜台/03-2_ST_NC_CC_NN.jpg)

![03 · 柜台 — ST / Eterna / GR Positive / GR Negative](docs/images/film-comparison/03_柜台/03-3_ST_E_GR正片_GR负片.jpg)

**04 · 旋转楼梯**

![04 · 旋转楼梯 — ST / FL / FL2 / FL3](docs/images/film-comparison/04_旋转楼梯/04-1_ST_FL_FL2_FL3.jpg)

![04 · 旋转楼梯 — ST / NC / CC / NN](docs/images/film-comparison/04_旋转楼梯/04-2_ST_NC_CC_NN.jpg)

![04 · 旋转楼梯 — ST / Eterna / GR Positive / GR Negative](docs/images/film-comparison/04_旋转楼梯/04-3_ST_E_GR正片_GR负片.jpg)

**05 · 书架**

![05 · 书架 — ST / FL / FL2 / FL3](docs/images/film-comparison/05_书架/05-1_ST_FL_FL2_FL3.jpg)

![05 · 书架 — ST / NC / CC / NN](docs/images/film-comparison/05_书架/05-2_ST_NC_CC_NN.jpg)

![05 · 书架 — ST / Eterna / GR Positive / GR Negative](docs/images/film-comparison/05_书架/05-3_ST_E_GR正片_GR负片.jpg)

**06 · 海报**

![06 · 海报 — ST / FL / FL2 / FL3](docs/images/film-comparison/06_海报/06-1_ST_FL_FL2_FL3.jpg)

![06 · 海报 — ST / NC / CC / NN](docs/images/film-comparison/06_海报/06-2_ST_NC_CC_NN.jpg)

![06 · 海报 — ST / Eterna / GR Positive / GR Negative](docs/images/film-comparison/06_海报/06-3_ST_E_GR正片_GR负片.jpg)

</details>

## 致谢

**特别感谢 [Michael（Hearts-Ace）](https://github.com/Hearts-Ace/sony-a7r5-custom-firmware)。** 本项目的色彩拟合算法、响应建模和相关算子实现，主要基于他的研究与代码，并针对 A7C II 进行适配和后续优化。他分享的训练工具、外观资源与研究资料，以及对相关成果使用的授权，为本项目的色彩工作提供了重要支持。

这是我的第一个开源项目，没想到能收到这么多关注和支持，真心谢谢大家。

- **合作者**：感谢 [@UzLung1435](https://github.com/UzLung1435) 贡献的 FL23 重构、USB 兼容性修复和照片／视频曲线分流（[#5](https://github.com/QAQLeonard/a7c2-tools/pull/5)、[#6](https://github.com/QAQLeonard/a7c2-tools/pull/6)），也感谢每一位提交 Issue、PR 和建议的朋友。
- **色彩**：感谢小红书 **门萨特里顿** 和 **爸总林先森** 提供 DCP，也感谢帮我拟合、比对色彩标准的网友。没有你们，就没有现在的内置外观。
- **参考与引用的项目**：本项目站在这些工作的肩膀上——
  - [Erlla/sony-a7m4-custom-firmware](https://github.com/Erlla/sony-a7m4-custom-firmware)：A7 IV 固件定制、卡刷与功能设置流程，为本项目的安装和资源适配提供参考。
  - [happyfrog2026/a7m4-color-research](https://github.com/happyfrog2026/a7m4-color-research) 及 [a74-recovery-tools](https://github.com/happyfrog2026/a74-recovery-tools)：色彩管线、创意外观名称／图标、回放标记及备份恢复研究与工具。
  - [Itinerary200/a7m4-lut](https://github.com/Itinerary200/a7m4-lut)：LUT 色彩空间转换与兼容传递曲线的参考。
  - [SONY-FW/a7c2-re](https://github.com/SONY-FW/a7c2-re) 及 [chocotan/a7c2-qemu](https://github.com/chocotan/a7c2-qemu)：A7C II 启动链、更新器、AP／CP 和虚拟机研究，支持本项目的底层分析与离线验证。
  - [DavidBuchanan314/ILCE-7M4-RE](https://github.com/DavidBuchanan314/ILCE-7M4-RE)：索尼相机启动、存储及 Fastboot 逆向研究。
  - [lzh2016zzz/a7cr-fl23-research](https://github.com/lzh2016zzz/a7cr-fl23-research)：A7CR 上的 FL2／FL3 移植研究，本项目参数、标签和 WBI 方法的起点。
  - [MDHan/a7c2-fl23-macos](https://github.com/MDHan/a7c2-fl23-macos)：A7C II 的 macOS 版本，Mac 上识别相机存储、接管 USB 的流程参考。
  - [ma1co/Sony-PMCA-RE](https://github.com/ma1co/Sony-PMCA-RE)、[ma1co/fwtool.py](https://github.com/ma1co/fwtool.py) 和 [YuuLuo/a7c2-service-preload](https://github.com/YuuLuo/a7c2-service-preload)：服务模式通信、固件解析和 A7C II 服务模式研究。
  - 也感谢所有引用、转载和二次开发本项目的开发者。
- **测试**：感谢愿意用自己的相机实机测试、耐心回传日志的各位。每一次反馈都让工具更安全。
- **大家**：感谢每一位点 Star、转发和在群里交流的朋友，是你们让这个项目走到了 3.0。

## 赞助

如果这个项目帮到了你，欢迎请我喝杯咖啡 ☕。赞助完全自愿，不影响任何功能，项目会一直免费开源。

<table>
  <tr>
    <td align="center"><img src="docs/images/sponsor/wechat.png" alt="微信支付收款码" width="200"><br>微信支付</td>
    <td align="center"><img src="docs/images/sponsor/alipay.png" alt="支付宝收款码" width="200"><br>支付宝</td>
    <td align="center"><img src="docs/images/sponsor/usdt-bep20.png" alt="USDT（BEP20）收款码" width="200"><br>USDT（BEP20）</td>
  </tr>
</table>

**USDT 地址**（仅限 **BNB Smart Chain／BEP20** 网络的 USDT）：

```text
0xbf0b2900f7a45a029a42013b90911f796735a753
```

> [!WARNING]
> 请只用 BEP20 网络转 USDT。其他网络或其他币种可能无法到账，也请不要向这个地址转 NFT。
