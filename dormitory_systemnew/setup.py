"""
智慧宿舍管理系统 - 安装程序
"""
from setuptools import setup, find_packages

setup(
    name='dormitory-system',
    version='2.0.0',
    description='智慧宿舍管理系统 - 企业级宿舍管理解决方案',
    author='Dormitory System Team',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'Flask>=3.0.0',
        'Flask-WTF>=1.2.1',
        'PyMySQL>=1.1.0',
        'DBUtils>=3.0.3',
        'pandas>=2.1.4',
        'openpyxl>=3.1.2',
        'python-dotenv>=1.0.0',
    ],
    python_requires='>=3.8',
    entry_points={
        'console_scripts': [
            'dormitory-system=app_new:main',
        ],
    },
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Education',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
    ],
)
