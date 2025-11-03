#!/usr/bin/env bash

PLAYLIST_URL="https://www.youtube.com/playlist?list=WL"
COOKIES="tmp/youtube_cookies.txt"
LAST_INDEX_FILE="last_index.txt"
VIDEOS_FILE="videos.tsv"
LOG_FILE="ytlog.txt"
START_INDEX=1

# Если уже есть сохранённый индекс — читаем его
if [ -f "$LAST_INDEX_FILE" ]; then
    START_INDEX=$(cat "$LAST_INDEX_FILE")
    echo "🔁 Продолжаем с индекса $START_INDEX"
else
    echo "▶️  Начинаем с начала"
fi

# Создаём (или очищаем) файлы
: > "$LOG_FILE"
touch "$VIDEOS_FILE"

# Запускаем yt-dlp и сохраняем вывод
yt-dlp \
  --cookies "$COOKIES" \
  --skip-download \
  --write-info-json \
  --write-description \
  --write-thumbnail \
  --print "%(playlist_index)s\t%(title)s\t%(webpage_url)s" \
  --playlist-start "$START_INDEX" \
  --newline \
  "$PLAYLIST_URL" \
  2>&1 | tee -a "$LOG_FILE" | while IFS=$'\t' read -r index title url; do

    # Если строка начинается с числа — значит это видео
    if [[ $index =~ ^[0-9]+$ ]]; then
        # Сохраняем индекс (чтобы знать, где остановились)
        echo "$index" > "$LAST_INDEX_FILE"

        # Добавляем запись о видео в TSV (index, title, url)
        echo -e "${index}\t${title}\t${url}" >> "$VIDEOS_FILE"
    fi
done

# Проверяем статус выполнения yt-dlp
if [ ${PIPESTATUS[0]} -eq 0 ]; then
    echo "✅ Завершено успешно. Удаляем $LAST_INDEX_FILE"
    rm -f "$LAST_INDEX_FILE"
else
    echo "⚠️ Ошибка! Последний индекс сохранён в $LAST_INDEX_FILE"
fi
