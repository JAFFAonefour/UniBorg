from telethon import events
import os
import subprocess
from hachoir.metadata import extractMetadata
from hachoir.parser import createParser
from PIL import Image


thumb_image_path = Config.TMP_DOWNLOAD_DIRECTORY + "/thumb_image.jpg"


@borg.on(events.NewMessage(pattern=r"\.savethumbnail", outgoing=True))
async def _(event):
    if event.fwd_from:
        return
    await event.edit("Processing ...")
    if not os.path.isdir(Config.TMP_DOWNLOAD_DIRECTORY):
        os.makedirs(Config.TMP_DOWNLOAD_DIRECTORY)
    if event.reply_to_msg_id:
        downloaded_file_name = await borg.download_media(
            await event.get_reply_message(),
            Config.TMP_DOWNLOAD_DIRECTORY
        )
        if downloaded_file_name.endswith(".mp4"):
            downloaded_file_name = get_video_thumb(downloaded_file_name)
        metadata = extractMetadata(createParser(downloaded_file_name))
        height = 0
        if metadata.has("height"):
            height = metadata.get("height")
        # resize image
        # ref: https://t.me/PyrogramChat/44663
        # https://stackoverflow.com/a/21669827/4723940
        Image.open(downloaded_file_name).convert("RGB").save(downloaded_file_name)
        img = Image.open(downloaded_file_name)
        # https://stackoverflow.com/a/37631799/4723940
        # img.thumbnail((90, 90))
        img.resize((90, height))
        img.save(thumb_image_path, "JPEG")
        # https://pillow.readthedocs.io/en/3.1.x/reference/Image.html#create-thumbnails
        os.remove(downloaded_file_name)
        await event.edit("Custom video / file thumbnail saved. This image will be used in the next upload.")
    else:
        await event.edit("Reply to a photo to save custom thumbnail")


@borg.on(events.NewMessage(pattern=r"\.clearthumbnail", outgoing=True))
async def _(event):
    if event.fwd_from:
        return
    if os.path.exists(thumb_image_path):
        os.remove(thumb_image_path)
    await event.edit("✅ Custom thumbnail cleared succesfully.")


def video_metadata(file):
    return extractMetadata(createParser(file))


def get_video_thumb(file, output=None, width=90):
    output = file + ".jpg"
    metadata = video_metadata(file)
    p = subprocess.Popen([
        'ffmpeg', '-i', file,
        '-ss', str(int((0, metadata.get('duration').seconds)[metadata.has('duration')] / 2)),
        # '-filter:v', 'scale={}:-1'.format(width),
        '-vframes', '1',
        output,
    ], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    p.communicate()
    if not p.returncode and os.path.lexists(file):
        os.remove(file)
        return output


@borg.on(events.NewMessage(pattern=r"\.getthumbnail", outgoing=True))
async def _(event):
    if event.fwd_from:
        return
    if event.reply_to_msg_id:
        r = await event.get_reply_message()
        try:
            a = await borg.download_media(
                r.media.document.thumbs[0],
                Config.TMP_DOWNLOAD_DIRECTORY
            )
        except Exception as e:
            await event.edit(str(e))
        try:
            await borg.send_file(
                event.chat_id,
                a,
                force_document=False,
                allow_cache=False,
                reply_to=event.reply_to_msg_id,
            )
            os.remove(a)
            await event.delete()
        except Exception as e:
            await event.edit(str(e))
    else:
        await event.edit("Reply `.gethumbnail` as a reply to a media")


