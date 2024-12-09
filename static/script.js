document.addEventListener("DOMContentLoaded", function() {
	// 获取播放按钮和音频元素
	// const playButton = document.getElementById("play-button");
	const audioPlayer = document.getElementById("audio-player");
	const audioSource = document.getElementById("audio-source");
	
	// 检查音频元素是否存在
    if (!audioPlayer || !audioSource) {
        console.error("Audio source or player element not found");
        return;
    }

	// 获取文本元素
	const textItems = document.querySelectorAll('.text-item');
	
	let currentIndex = -1;
	
	/// <begin>切换语言
	
	// 获取切换语言按钮
	const toggleButton = document.getElementById("toggle-language-btn");

	let isChinese = 0;  // 0: 英文, 1: 中文, 2: 无文本模式

	// 切换中英文与无文本模式
	function toggleLanguage() {
	isChinese = (isChinese + 1) % 3;  // 循环 0, 1, 2

	textItems.forEach(item => {
		const textZh = item.getAttribute("data-text-zh");
		const textEn = item.getAttribute("data-text");

		// 根据当前语言显示中文、英文或无文本
		if (isChinese === 0) {
		item.textContent = textEn;
		} else if (isChinese === 1) {
		item.textContent = textZh;
		} else {
		item.textContent = "";
		}
	});

	// 更新按钮文本并改变背景色
	if (isChinese === 0) {
		toggleButton.textContent = "EN";  // 英文模式
		toggleButton.className = "en";    // 设置按钮的背景颜色为蓝色
	} else if (isChinese === 1) {
		toggleButton.textContent = "ZH";  // 中文模式
		toggleButton.className = "zh";    // 设置按钮的背景颜色为红色
	} else {
		toggleButton.textContent = "NU";  // 无文本模式
		toggleButton.className = "nu";    // 设置按钮的背景颜色为黑色
	}
	}

	// 给按钮添加点击事件监听器
	toggleButton.addEventListener("click", toggleLanguage);


	/// <end>切换语言

	/// <begin>播放下一个音频

	function playNextAudio() {
		var audio_name = document.title;

		currentIndex++;

		// 防止越界
        if (currentIndex >= textItems.length) {
            console.log("播放结束，没有更多音频。");
            return;
        }

		// 获取当前文本项的音频文件
		const audioFile = textItems[currentIndex].getAttribute('data-audio');
			
		// 延迟 500 毫秒后播放音频
		setTimeout(() => {
			// 设置音频源并加载
			audioSource.src = `../../result/${audio_name}/segments/${audioFile}`;
			audioPlayer.load();
			audioPlayer.play();
			
			// 更新文本项的样式
			textItems.forEach(item => item.classList.remove('playing'));
			textItems[currentIndex].classList.add('playing');
		}, 500); // 500 毫秒的延迟
	}

	// 当点击文本时，播放对应音频
	textItems.forEach((item, index) => {
		item.addEventListener("click", function() {
			currentIndex = index - 1;
			playNextAudio();
		});
	});

	// 监听音频播放结束事件，自动播放下一个音频
	audioPlayer.addEventListener('ended', playNextAudio);

	/// <end>播放下一个音频
});
