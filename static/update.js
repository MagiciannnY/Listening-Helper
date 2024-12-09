function uploadFile() {
  var formData = new FormData(document.getElementById('uploadForm'));
  fetch('/upload', {
      method: 'POST',
      body: formData
  })
  .then(response => response.text())
  .then(data => {
      alert(data); // 显示服务器返回的信息
  })
  .catch(error => {
      console.error('Error:', error);
  });

  // 阻止表单默认提交行为
  return false;
}
