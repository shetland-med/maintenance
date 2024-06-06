document.addEventListener('DOMContentLoaded', function () {
    var newsDataElement = document.getElementById('news-data');
    var appsDataElement = document.getElementById('apps-data');
    var filteredAppsDataElement = document.getElementById('filter-apps');

    if (newsDataElement && appsDataElement && filteredAppsDataElement) {
        var newsData = JSON.parse(newsDataElement.textContent);
        var appsData = JSON.parse(appsDataElement.textContent);
        var filteredAppsData = JSON.parse(filteredAppsDataElement.textContent);

        new Vue({
            el: '#app',
            delimiters: ['${', '}'], // Vue.jsのデリミタを変更
            data: {
                appsData: appsData,
                filteredAppsData: filteredAppsData,
                selectedNews: newsData.map(news => ({ 
                    original: { ...news }, // 元のデータを保存
                    current: { ...news }, // 編集可能なデータ
                    changed: false, 
                    changedCells: [], 
                    file: null,
                    newRow: false // 新規追加された行かどうかのフラグ
                })),
                displayedNews: [], // 表示するニュースのリスト
                selectedApps: [],
                showModal: false,
                displayApps: ""
            },
            created() {
                this.displayedNews = [...this.selectedNews];
                this.selectedApps = [...this.filteredAppsData];
                this.displayApps = this.selectedApps.join(', ');
            },
            methods: {
                toggleModal() {
                    this.showModal = !this.showModal;
                },
                cancelSearch() {
                    this.showModal = false;
                },
                applyFilter() {
                    this.showModal = false;
                    if (this.selectedApps.length === 0) {
                        this.displayedNews = [...this.selectedNews];
                    } else {
                        this.displayedNews = this.selectedNews.filter(news => this.selectedApps.includes(news.current[0]));
                    }
                    this.displayApps = this.selectedApps.join(', ');
                },
                addRow() {
                    const newRow = {
                        original: {
                            0: '',
                            1: '',
                            2: '',
                            3: '',
                            4: '',
                            5: '',
                            6: '',
                            7: 0,
                            8: ''
                        },
                        current: {
                            0: '',
                            1: '',
                            2: '',
                            3: '',
                            4: '',
                            5: '',
                            6: '',
                            7: 0,
                            8: ''
                        },
                        changed: true,
                        changedCells: [],
                        file: null,
                        newRow: true // 新規追加された行
                    };
                    this.selectedNews.push(newRow);
                    this.applyFilter(); // フィルターを再適用
                },
                markChanged(news, cellIndex, event = null) {
                    if (news.newRow) {
                        if (cellIndex === 6 && event) {
                            const file = event.target.files[0];
                            news.file = file;
                            news.current[cellIndex] = file.name;
                        }
                        return; // 新規追加された行は変更マークを付けない
                    }

                    let newValue = news.current[cellIndex];
                    let originalValue = news.original[cellIndex];

                    if (cellIndex === 6 && event) {
                        const file = event.target.files[0];
                        news.file = file;
                        newValue = file.name;
                    } else if (cellIndex === 7) {
                        newValue = news.current[7] ? 1 : 0;
                    }

                    if (newValue !== originalValue) {
                        if (!news.changedCells.includes(cellIndex)) {
                            news.changedCells.push(cellIndex);
                        }
                        news.current[cellIndex] = newValue;
                        news.changed = true;
                    } else {
                        news.changedCells = news.changedCells.filter(index => index !== cellIndex);
                        news.current[cellIndex] = newValue;
                        if (news.changedCells.length === 0) {
                            news.changed = false;
                        }
                    }

                    // Check if all cells are back to original values, if so, reset changed state
                    if (news.changed && Object.keys(news.current).every(key => news.current[key] === news.original[key])) {
                        news.changed = false;
                    }
                },
                registerChanges() {
                    const changedNews = this.selectedNews.filter(news => news.changed);
                    const formData = new FormData();

                    // 必須項目チェック
                    for (let news of changedNews) {
                        if (Object.values(news.current).some((value, index) => index !== 7 && !value)) {
                            alert('すべての必須項目を入力してください。');
                            return;
                        }
                    }

                    changedNews.forEach((news, index) => {
                        if (news.file) {
                            formData.append(`file_${index}`, news.file);
                        }
                        formData.append(`news_${index}`, JSON.stringify(news.current));
                    });

                    axios.post('/register', formData, {
                        headers: {
                            'Content-Type': 'multipart/form-data'
                        }
                    })
                    .then(response => {
                        if (response.data.status === 'success') {
                            alert('登録に成功しました');
                            this.selectedNews.forEach(news => {
                                if (news.changed) {
                                    news.original = { ...news.current };
                                    news.changed = false;
                                    news.changedCells = [];
                                    news.newRow = false; // 新規追加行のフラグをリセット
                                }
                            });
                            this.applyFilter(); // フィルターを再適用
                        } else {
                            alert('登録に失敗しました: ' + response.data.message);
                        }
                    })
                    .catch(error => {
                        alert('登録中にエラーが発生しました: ' + error);
                    });
                }
            }
        });
    } else {
        console.error('Required elements are missing.');
    }
});
