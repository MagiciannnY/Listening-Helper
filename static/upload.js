document.addEventListener('DOMContentLoaded', function() {
    // 拖拽文件
    const dropZone = document.getElementById('drop-zone');
    var selectButton = document.getElementById('selectbtn1');
    var audioFileInput = document.getElementById('audio-file');
    var fileList = document.getElementById('file-list');
    const file_zone = document.getElementById('file-zone');
    
    // 添加拖拽事件监听器
    dropZone.addEventListener('dragover', (event) => {
        event.preventDefault();
        dropZone.classList.add('drag-over');
    });
    
    dropZone.addEventListener('dragleave', (event) => {
        dropZone.classList.remove('drag-over');
    });
    
    dropZone.addEventListener('drop', (event) => {
        event.preventDefault();
        dropZone.classList.remove('drag-over');
        const files = event.dataTransfer.files;
        handleFiles(files);
        alert(`已拖入 ${files.length} 个文件`);
    });

    function handleFiles(files) {
        file_zone.style.display = 'flex'; // 显示文件区域
        fileList.innerHTML = ''; // 清空现有的文件列表
        fileList.textContent = files[0].name;

        // 创建一个 DataTransfer 对象以更新 input 的 files
        const dataTransfer = new DataTransfer();
        Array.from(files).forEach((file) => dataTransfer.items.add(file));
        audioFileInput.files = dataTransfer.files;
    }
    
    // 选择文件

    selectButton.addEventListener('click', function(){
        audioFileInput.click();
    });

    audioFileInput.addEventListener('change', function(event) {
        var files = event.target.files;
        var file_zone = document.getElementById('file-zone');
        if (files.length > 0) {
            file_zone.style.display = 'flex';
            file_zone.style.color = 'white';
            file_zone.style.fontWeight = 'bold';
            file_zone.style.fontSize = '20px';
            fileList.innerHTML = '';
            var ul = document.getElementById('file-list');
            ul.textContent = files[0].name;
        }
    });
});