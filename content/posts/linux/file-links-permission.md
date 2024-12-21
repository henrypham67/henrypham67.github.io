---
title: 'File - Link'
date: 2024-10-26T16:00:33+07:00
draft: true
---

## Links

### Hard links

- Additional name for existing file
- NOT for directory
- NOT cross filesystem boundaries/partitions
- Same inode number & permissions as original file

### Soft link

- A file point to another file
- CAN be create for directories
- CAN cross filesystem boundaries/partitions
- Differnt inode number and file permissions than original
- Does NOT contain file data

## File/Directory Permissions

## Positions

from `ls -l` command

1     : -/d/l -> file/directory/links \
2,3,4 : read, write, execute for user (owner) \
5,6,7 : ------------------------ group \
8,9,10: ------------------------ other (world) \
11    : SELinux security context (.); Any other alternate access method (+)

```
Why .pem permission is 400?
```
### umask
