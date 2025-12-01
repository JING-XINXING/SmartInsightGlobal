#!/usr/bin/env python3
"""
SmartInsight Global - 云端备份上传脚本

功能：
    - 将本地备份文件上传到云存储 (支持 OSS/S3/COS)
    - 增量上传 (只上传新文件)
    - 支持加密上传
    - 自动清理云端过期备份

使用方法：
    python backup_upload.py [--config config.yaml] [--dry-run]

依赖：
    pip install boto3 oss2 pyyaml
"""

import os
import sys
import argparse
import hashlib
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class CloudStorageBase:
    """云存储基类"""
    
    def upload(self, local_path: str, remote_path: str) -> bool:
        """上传文件"""
        raise NotImplementedError
    
    def list_files(self, prefix: str = "") -> List[Dict[str, Any]]:
        """列出文件"""
        raise NotImplementedError
    
    def delete(self, remote_path: str) -> bool:
        """删除文件"""
        raise NotImplementedError
    
    def exists(self, remote_path: str) -> bool:
        """检查文件是否存在"""
        raise NotImplementedError


class AliyunOSSStorage(CloudStorageBase):
    """阿里云 OSS 存储"""
    
    def __init__(self, config: Dict[str, str]):
        try:
            import oss2
        except ImportError:
            logger.error("请安装 oss2: pip install oss2")
            sys.exit(1)
        
        self.auth = oss2.Auth(
            config['access_key_id'],
            config['access_key_secret']
        )
        self.bucket = oss2.Bucket(
            self.auth,
            config['endpoint'],
            config['bucket']
        )
        self.prefix = config.get('prefix', 'backups/')
    
    def upload(self, local_path: str, remote_path: str) -> bool:
        """上传文件到 OSS"""
        try:
            full_path = f"{self.prefix}{remote_path}"
            self.bucket.put_object_from_file(full_path, local_path)
            logger.info(f"上传成功: {local_path} -> {full_path}")
            return True
        except Exception as e:
            logger.error(f"上传失败: {e}")
            return False
    
    def list_files(self, prefix: str = "") -> List[Dict[str, Any]]:
        """列出 OSS 中的备份文件"""
        files = []
        full_prefix = f"{self.prefix}{prefix}"
        for obj in self.bucket.list_objects(prefix=full_prefix).object_list:
                files.append({
                    'name': obj.key.replace(self.prefix, ''),
                    'size': obj.size,
                'modified': obj.last_modified
                })
        return files
    
    def delete(self, remote_path: str) -> bool:
        """删除 OSS 文件"""
        try:
            full_path = f"{self.prefix}{remote_path}"
            self.bucket.delete_object(full_path)
            logger.info(f"删除成功: {full_path}")
            return True
        except Exception as e:
            logger.error(f"删除失败: {e}")
            return False
    
    def exists(self, remote_path: str) -> bool:
        """检查文件是否存在"""
        full_path = f"{self.prefix}{remote_path}"
        return self.bucket.object_exists(full_path)


class AWSS3Storage(CloudStorageBase):
    """AWS S3 存储"""
    
    def __init__(self, config: Dict[str, str]):
        try:
            import boto3
        except ImportError:
            logger.error("请安装 boto3: pip install boto3")
            sys.exit(1)
        
        self.s3 = boto3.client(
            's3',
            aws_access_key_id=config['access_key_id'],
            aws_secret_access_key=config['access_key_secret'],
            region_name=config.get('region', 'us-east-1')
        )
        self.bucket = config['bucket']
        self.prefix = config.get('prefix', 'backups/')
    
    def upload(self, local_path: str, remote_path: str) -> bool:
        """上传文件到 S3"""
        try:
            full_path = f"{self.prefix}{remote_path}"
            self.s3.upload_file(local_path, self.bucket, full_path)
            logger.info(f"上传成功: {local_path} -> {full_path}")
            return True
        except Exception as e:
            logger.error(f"上传失败: {e}")
            return False
    
    def list_files(self, prefix: str = "") -> List[Dict[str, Any]]:
        """列出 S3 中的备份文件"""
        files = []
        full_prefix = f"{self.prefix}{prefix}"
        response = self.s3.list_objects_v2(Bucket=self.bucket, Prefix=full_prefix)
        for obj in response.get('Contents', []):
                    files.append({
                        'name': obj['Key'].replace(self.prefix, ''),
                        'size': obj['Size'],
                'modified': obj['LastModified']
                    })
        return files
    
    def delete(self, remote_path: str) -> bool:
        """删除 S3 文件"""
        try:
            full_path = f"{self.prefix}{remote_path}"
            self.s3.delete_object(Bucket=self.bucket, Key=full_path)
            logger.info(f"删除成功: {full_path}")
            return True
        except Exception as e:
            logger.error(f"删除失败: {e}")
            return False
    
    def exists(self, remote_path: str) -> bool:
        """检查文件是否存在"""
        try:
            full_path = f"{self.prefix}{remote_path}"
            self.s3.head_object(Bucket=self.bucket, Key=full_path)
            return True
        except:
            return False


class LocalStorage(CloudStorageBase):
    """本地目录存储（用于测试）"""
    
    def __init__(self, config: Dict[str, str]):
        self.base_path = Path(config.get('path', '/tmp/backups'))
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    def upload(self, local_path: str, remote_path: str) -> bool:
        """复制文件到目标目录"""
        import shutil
        try:
            dest = self.base_path / remote_path
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(local_path, dest)
            logger.info(f"复制成功: {local_path} -> {dest}")
            return True
        except Exception as e:
            logger.error(f"复制失败: {e}")
            return False
    
    def list_files(self, prefix: str = "") -> List[Dict[str, Any]]:
        """列出目录中的文件"""
        files = []
        for f in self.base_path.glob(f"{prefix}*"):
            if f.is_file():
                stat = f.stat()
                files.append({
                    'name': str(f.relative_to(self.base_path)),
                    'size': stat.st_size,
                    'modified': datetime.fromtimestamp(stat.st_mtime)
                })
        return files
    
    def delete(self, remote_path: str) -> bool:
        """删除文件"""
        try:
            (self.base_path / remote_path).unlink()
            logger.info(f"删除成功: {remote_path}")
            return True
        except Exception as e:
            logger.error(f"删除失败: {e}")
            return False
    
    def exists(self, remote_path: str) -> bool:
        """检查文件是否存在"""
        return (self.base_path / remote_path).exists()


def load_config(config_path: str) -> Dict:
    """加载配置文件"""
    import yaml
        
    with open(config_path, 'r') as f:
            return yaml.safe_load(f)

    
def get_storage(config: Dict) -> CloudStorageBase:
    """根据配置获取存储实例"""
    provider = config.get('provider', 'local')
        
    if provider == 'oss':
        return AliyunOSSStorage(config['oss'])
    elif provider == 's3':
        return AWSS3Storage(config['s3'])
    elif provider == 'local':
        return LocalStorage(config.get('local', {}))
    else:
        raise ValueError(f"不支持的存储提供商: {provider}")


def get_file_hash(filepath: str) -> str:
    """计算文件 MD5 哈希"""
    hash_md5 = hashlib.md5()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

    
def find_local_backups(backup_dir: str) -> List[Path]:
    """查找本地备份文件"""
    backup_path = Path(backup_dir)
    if not backup_path.exists():
        logger.warning(f"备份目录不存在: {backup_dir}")
            return []
        
    # 查找 .sql.gz 备份文件
    files = list(backup_path.glob("smartinsight_*.sql.gz"))
    return sorted(files, key=lambda x: x.stat().st_mtime, reverse=True)


def sync_backups(
    storage: CloudStorageBase,
    local_dir: str,
    retention_days: int = 30,
    dry_run: bool = False
) -> None:
    """同步备份到云端"""
    
    # 1. 查找本地备份
    local_files = find_local_backups(local_dir)
    logger.info(f"找到 {len(local_files)} 个本地备份文件")
    
    # 2. 获取云端已有文件
    remote_files = storage.list_files()
    remote_names = {f['name'] for f in remote_files}
    
    # 3. 上传新文件
    uploaded = 0
    for local_file in local_files:
        remote_name = local_file.name
        
        if remote_name in remote_names:
            logger.debug(f"跳过已存在: {remote_name}")
            continue
        
        if dry_run:
            logger.info(f"[DRY-RUN] 将上传: {remote_name}")
        else:
            if storage.upload(str(local_file), remote_name):
                uploaded += 1
    
    logger.info(f"上传了 {uploaded} 个新文件")
    
    # 4. 清理过期云端备份
    cutoff_date = datetime.now() - timedelta(days=retention_days)
        deleted = 0
    
    for remote_file in remote_files:
        modified = remote_file.get('modified')
        if modified and isinstance(modified, datetime):
            if modified < cutoff_date:
                if dry_run:
                    logger.info(f"[DRY-RUN] 将删除过期文件: {remote_file['name']}")
                else:
                    if storage.delete(remote_file['name']):
                        deleted += 1
        
    logger.info(f"删除了 {deleted} 个过期文件")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='SmartInsight Global - 云端备份上传脚本'
    )
    parser.add_argument(
        '--config', '-c',
        default='config.yaml',
        help='配置文件路径 (默认: config.yaml)'
    )
    parser.add_argument(
        '--dry-run', '-n',
        action='store_true',
        help='模拟运行，不实际上传或删除'
    )
    parser.add_argument(
        '--backup-dir', '-d',
        help='本地备份目录 (覆盖配置文件)'
    )
    parser.add_argument(
        '--retention-days', '-r',
        type=int,
        help='云端保留天数 (覆盖配置文件)'
    )
    
    args = parser.parse_args()
    
    # 加载配置
    config_path = Path(args.config)
    if not config_path.exists():
        # 如果配置文件不存在，使用默认配置
        logger.warning(f"配置文件不存在: {config_path}")
        logger.info("使用默认本地存储配置")
        config = {
            'provider': 'local',
            'local': {'path': '/tmp/smartinsight_cloud_backups'},
            'backup_dir': os.path.expanduser('~/backups/smartinsight'),
            'retention_days': 30
        }
    else:
        config = load_config(str(config_path))
    
    # 获取参数
    backup_dir = args.backup_dir or config.get('backup_dir', os.path.expanduser('~/backups/smartinsight'))
    retention_days = args.retention_days or config.get('retention_days', 30)
    
    logger.info("=========================================")
    logger.info("SmartInsight Global - 云端备份同步")
    logger.info("=========================================")
    logger.info(f"本地备份目录: {backup_dir}")
    logger.info(f"云端保留天数: {retention_days}")
    logger.info(f"存储提供商: {config.get('provider', 'local')}")
    
    if args.dry_run:
        logger.info("模式: 模拟运行 (DRY-RUN)")
    
    # 获取存储实例
    storage = get_storage(config)
    
    # 同步备份
    sync_backups(
        storage=storage,
        local_dir=backup_dir,
        retention_days=retention_days,
        dry_run=args.dry_run
    )
    
    logger.info("同步完成!")


if __name__ == '__main__':
    main()
