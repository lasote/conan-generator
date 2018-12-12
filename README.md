Conanfiles testing graph generator
==================================

This script creates in a temporary folder (and in an isolated Conan cache) conanfiles for a graph that you can describe in a 
text file. It will create for you the conanfiles in subfolders and will call `conan create` for each one.

This script is useful debugging some Conan issues when creating a test can be more tedious.

How to use
----------

Write a text file declaring the graph.
For the nodes you can use full references or just package names that will be defaulted to "1.0@user/testing".

The `->` are requires. The `~>` are `build_requires`

```
LIB_A -> LIB_B
LIB_M/1.0@conan/stable -> LIB_J
LIB_A ~> BR1
LIB_E -> LIB_A
LIB_F -> LIB_A
PROJECT -> LIB_E
PROJECT -> LIB_F
```


Run the script:

`python run.py graph.txt`


The script will tell you how to use the generated Conan cache and where are the created packages:

```
export CONAN_USER_HOME=/tmp/tmpf7627o04 && cd /tmp/tmp714cfhgz
```

In the tmp folder we can see folders for the generated packages:

```
$ ls

BR1_1.0_user_channel  
LIB_A_1.0_user_channel 
LIB_B_1.0_user_channel  
LIB_E_1.0_user_channel  
LIB_F_1.0_user_channel  
LIB_J_1.0_user_channel  
LIB_M_1.0_conan_stable  
PROJECT_1.0_user_channel
```