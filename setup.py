import setuptools

setuptools.setup(
    name="magic-online-game-history-recorder",
    version="0.1",
    author="Pedrogush",
    author_email="pedrogush@gmail.com",
    description="ligamagic automation",
    packages=[],
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: Windows"
    ],
    python_requires=">=3.11",
    install_requires=[
        "opencv-python>=4.0",
        "tqdm",
        "numpy",
        "pyautogui",
        "pillow",
        'loguru',
        'psutil',
        "pytesseract",
        "pymongo",
        "pynput",
        "keyboard"
    ]
)