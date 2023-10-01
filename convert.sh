for f in convertSounds/*; do
	ffmpeg -i "$f" -map_metadata -1 -c:a libopus -b:a 64k -vbr on -compression_level 10 converted/${f##*/}
done
