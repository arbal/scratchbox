version:
	gcc --version
	clang --version
	capnp --version

requirements:
	sudo apt install -y capnproto libcapnp-dev
	sudo apt install -y cmake clang libclang-dev llvm llvm-dev libc++1 libc++-dev libc++abi-dev

# no explicit selection of c++ stdlib
build_cppyy_clang:
	CC=`which clang` \
	CXX=`which clang++` \
	CXXFLAGS="-std=c++11" \
	MAKE_NPROCS=4 \
	~/pypy-5.6-linux_x86_64-portable/bin/pip install --no-cache-dir --verbose PyPy-cppyy-backend

# explicit selection of new libc++ c++ stdlib
build_cppyy_clang_libc:
	CC=`which clang` \
	CXX=`which clang++` \
	CXXFLAGS="-std=c++11 -stdlib=libc++" \
	LDFLAGS="-stdlib=libc++" \
	MAKE_NPROCS=4 \
	~/pypy-5.6-linux_x86_64-portable/bin/pip install --no-cache-dir --verbose PyPy-cppyy-backend

# explicit selection of GNU c++ stdlib
build_cppyy_clang_stdc:
	CC=`which clang` \
	CXX=`which clang++` \
	CXXFLAGS="-std=c++11 -stdlib=libstdc++" \
	LDFLAGS="-stdlib=libstdc++" \
	MAKE_NPROCS=4 \
	~/pypy-5.6-linux_x86_64-portable/bin/pip install --no-cache-dir --verbose PyPy-cppyy-backend

build_cppyy_gcc:
	CC=`which gcc-4.9` \
	CXX=`which g++-4.9` \
	MAKE_NPROCS=4 \
	~/pypy-5.6-linux_x86_64-portable/bin/pip install -no-cache-dir --verbose PyPy-cppyy-backend

generate:
	capnp compile -oc++ addressbook.capnp

compile: generate
	g++ -std=c++11 -c test.cpp

link_dynamic:
	g++ test.o -lcapnp -lkj -o test
	file ./test
	ldd ./test

link_static:
	#g++ test.o -Wl,-Bstatic -lcapnp -lkj -o test
	#g++ test.o /usr/lib/x86_64-linux-gnu/libcapnp.a /usr/lib/x86_64-linux-gnu/libkj.a -o test
	#g++ -static -static-libgcc -static-libstdc++ test.o -lcapnp -lkj -o test
	g++ -static test.o -lcapnp -lkj -o test
	file ./test
	-ldd ./test
	nm ./test | grep " U "

build_dynamic: compile link_dynamic

build_static: compile link_static

clean:
	rm ./*.so
	rm -f addressbook.capnp.c++
	rm -f addressbook.capnp.h
	rm -f addressbook.dat
	rm -f test
	rm -f test.o
	rm -f MyClass_rflx.cpp
	rm -f MyClass_rflx_rdict.pcm

build: clean build_static build_dynamic

