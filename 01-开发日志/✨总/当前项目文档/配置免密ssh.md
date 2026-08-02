260731

```
lin@lin-virtual-machine:~$ ssh-keygen -t ed25519 -C "lin@192.168.1.204"
Generating public/private ed25519 key pair.
Enter file in which to save the key (/home/lin/.ssh/id_ed25519): 
/home/lin/.ssh/id_ed25519 already exists.
Overwrite (y/n)? 
lin@lin-virtual-machine:~$ grep -r IdentityFile ~/.ssh/config 2>/dev/null
lin@lin-virtual-machine:~$ ssh lin@192.168.1.210 echo ok
lin@192.168.1.210's password: 

lin@lin-virtual-machine:~$ ssh-keygen -t ed25519 -C "lin@192.168.1.204"
Generating public/private ed25519 key pair.
Enter file in which to save the key (/home/lin/.ssh/id_ed25519): 
/home/lin/.ssh/id_ed25519 already exists.
Overwrite (y/n)? y
Enter passphrase (empty for no passphrase): 
Enter same passphrase again: 
Your identification has been saved in /home/lin/.ssh/id_ed25519
Your public key has been saved in /home/lin/.ssh/id_ed25519.pub
The key fingerprint is:
SHA256:QCmZWdPBsVf1mCD8/9zpnnpw2XLNXQEe7Vk79setcbI lin@192.168.1.204
The key's randomart image is:
+--[ED25519 256]--+
|     =++o+. o++  |
|    =...o..o...*.|
|     .. . .. .+ *|
|       . .  .  *.|
|        S    ..oX|
|             .=o%|
|              o@+|
|              Eo=|
|             .=+ |
+----[SHA256]-----+
lin@lin-virtual-machine:~$ 
lin@lin-virtual-machine:~$ ssh-copy-id -i ~/.ssh/id_ed25519.pub lin@192.168.1.210
/usr/bin/ssh-copy-id: INFO: Source of key(s) to be installed: "/home/lin/.ssh/id_ed25519.pub"
/usr/bin/ssh-copy-id: INFO: attempting to log in with the new key(s), to filter out any that are already installed
/usr/bin/ssh-copy-id: INFO: 1 key(s) remain to be installed -- if you are prompted now it is to install the new keys
lin@192.168.1.210's password: 

Number of key(s) added: 1

Now try logging into the machine, with:   "ssh 'lin@192.168.1.210'"
and check to make sure that only the key(s) you wanted were added.

lin@lin-virtual-machine:~$ 

```

