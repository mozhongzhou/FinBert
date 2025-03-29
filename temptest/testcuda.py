import torch

def check_cuda():
    print("检查 CUDA 可用性...")

    # 检查 PyTorch 是否支持 CUDA
    if torch.version.cuda is None:
        print("❌ PyTorch 未编译 CUDA 支持")
        print("当前 PyTorch 版本不支持 CUDA。请安装支持 CUDA 的 PyTorch 版本。")
        print("安装示例（以 CUDA 11.8 为例）：")
        print("pip install torch --extra-index-url https://download.pytorch.org/whl/cu118")
        print("请访问 https://pytorch.org/get-started/locally/ 根据你的 CUDA 版本选择合适的命令。")
    else:
        print(f"✅ PyTorch 支持 CUDA，版本：{torch.version.cuda}")

    # 检查系统上是否有可用的 CUDA 设备
    if torch.cuda.is_available():
        print("✅ CUDA 设备可用")
        print(f"CUDA 设备数量: {torch.cuda.device_count()}")
        for i in range(torch.cuda.device_count()):
            print(f"设备 {i}: {torch.cuda.get_device_name(i)}")
    else:
        print("❌ CUDA 设备不可用")
        print("请检查以下几点：")
        print("1. 是否安装了 NVIDIA 驱动？")
        print("2. 是否安装了 CUDA 工具包？")
        print("3. 系统上是否有可用的 NVIDIA GPU？")
        print("4. PyTorch 支持的 CUDA 版本是否与系统上的 CUDA 版本兼容？")

if __name__ == "__main__":
    check_cuda()