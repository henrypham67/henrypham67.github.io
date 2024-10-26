# Permissions

## chown

change owner
can it be used to change group?

## chgrp

prerequisites?

cmd `group` to list existing groups

## rwx

when to give other permissions?

best practices?

the first position

```text
d
-
c
l
s
p
b
```

## SUID

set user ID bit \
-> exec as the id of the owner instead of the person who is running \
`chmod 4664 suidfile`
`---s------` -> SUID with execute permission
`-r-S------` -> SUID without execute permission

## SGID

the same to *SUID* but apply for group
`chmod 2664 suidfile`

`chmod 6664 suidfile` for both SUID & SGID

the same principles apply to directory

```bash
ls -ld stickydir 
drwxrwxr-x 2 henry henry 4096 Jun 25 07:13 stickydir


chmod 1666 stickydir 
ls -ld stickydir
drw-rw-rwT 2 henry henry 4096 Jun 25 07:13 stickydir


chmod 1777 stickydir 
ls -ld stickydir
drwxrwxrwt 2 henry henry 4096 Jun 25 07:13 stickydir
```

## sticky bit
