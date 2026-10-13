"""Selected original bytes and attributed derivatives; no network ingestion."""
import hashlib
import mimetypes
import os
from pathlib import Path
import re
import shutil
import tempfile
from urllib.parse import urlsplit

MAX_BYTES = 256 * 1024 * 1024
HASH = re.compile(r'[a-f0-9]{64}\Z')
EXTENSIONS = {'audio/wav':'.wav','audio/x-wav':'.wav','audio/ogg':'.ogg','audio/mpeg':'.mp3','audio/mp4':'.m4a',
              'audio/flac':'.flac','video/mp4':'.mp4','image/png':'.png','image/jpeg':'.jpg','image/webp':'.webp',
              'text/plain':'.txt','text/markdown':'.md','application/pdf':'.pdf'}

def content_path(attachment):
    if not HASH.fullmatch(attachment['sha256']): raise ValueError('Invalid object digest')
    path = 'media/'+attachment['sha256']+EXTENSIONS.get(attachment['media_type'],'.bin')
    if attachment.get('content_path',path) != path: raise ValueError('Original content path does not match its digest/type')
    return path

def url(value):
    parsed = urlsplit(value)
    if parsed.scheme not in ('http','https') or not parsed.hostname or parsed.username or parsed.password or any(ord(c)<32 for c in value):
        raise ValueError('Use an HTTP(S) source without credentials')
    return value

def object_path(directory, sha256):
    if not HASH.fullmatch(sha256): raise ValueError('Invalid object digest')
    return Path(directory)/'objects'/sha256

def verify(directory, attachment):
    path = object_path(directory,attachment['sha256'])
    if path.is_symlink() or not path.is_file(): raise ValueError('Missing original object')
    hasher = hashlib.sha256(); size = 0
    with path.open('rb') as stream:
        while block := stream.read(1024*1024): hasher.update(block); size += len(block)
    if size != attachment['size'] or hasher.hexdigest() != attachment['sha256']:
        raise ValueError('Original object integrity check failed')
    return path

def retain(directory, source, media_type=None, max_bytes=MAX_BYTES):
    source = Path(source)
    if source.is_symlink() or not source.is_file(): raise ValueError('Select an original regular file')
    objects = Path(directory)/'objects'; objects.mkdir(exist_ok=True,mode=0o700)
    descriptor, temporary = tempfile.mkstemp(prefix='.incoming-',dir=objects)
    try:
        hasher = hashlib.sha256(); size = 0
        with os.fdopen(descriptor,'wb') as output, source.open('rb') as stream:
            while block := stream.read(1024*1024):
                size += len(block)
                if size > max_bytes: raise ValueError('Original exceeds the selected byte limit')
                hasher.update(block); output.write(block)
            output.flush(); os.fsync(output.fileno())
        selected_type = media_type or mimetypes.guess_type(source.name)[0] or 'application/octet-stream'
        if not re.fullmatch(r'[a-zA-Z0-9.+-]+/[a-zA-Z0-9.+-]+',selected_type): raise ValueError('Invalid media type')
        attachment = {'sha256':hasher.hexdigest(), 'size':size, 'media_type':selected_type, 'original_name':source.name}
        attachment['content_path'] = content_path(attachment)
        destination = object_path(directory,attachment['sha256'])
        if destination.exists(): verify(directory,attachment)
        else:
            # Link makes concurrent identical retains safe; neither can overwrite an object.
            try: os.link(temporary,destination)
            except FileExistsError: verify(directory,attachment)
        return attachment
    finally:
        Path(temporary).unlink(missing_ok=True)

def attachments(package):
    return [e['attachment'] for e in package['entries'] if 'attachment' in e] + [a['attachment'] for a in package.get('annotations',[]) if 'attachment' in a]

def export_objects(directory, packages, output):
    selected = {}
    for package in packages:
        for attachment in attachments(package):
            selected[attachment['sha256']] = verify(directory,attachment)
    target = Path(output)/'media'; target.mkdir(exist_ok=True)
    names = set()
    for package in packages:
        for attachment in attachments(package):
            filename = content_path(attachment).split('/')[1]; names.add(filename)
            source = selected[attachment['sha256']]
        # Bytes remain unchanged; publisher supplies attachment isolation and audience.
            shutil.copyfile(source,target/filename)
    for previous in target.iterdir():
        if previous.is_file() and previous.name not in names: previous.unlink()
