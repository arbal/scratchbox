# Storage Configuration

With all of below configuraiton variants, the 24 external HDDs are configured as a software RAID-60. This provides extremely high data integrity and security.

This **Archive Storage Subsystem** is then used for:

* long-term archival of received flat-files
* database and system backups

Further, of the 12 internal Intel DC S3700 SATA SSDs, two are used in a software RAID-1 (mirror) formatted with Btrfs as primary system disk.

This **System Storage Subsystem** is used for:

* boot disk
* OS
* OS containers

*The storage configurations below differ in how we make use of the (remaining) 10 internal Intel DC S3700 SATA SSDs and the 8 Intel P3700 NVMe SSDs.*


## Storage Configuration A

In this variant, two independent PostgreSQL database clusters are run:

* Work Database
* Results Database

The **Work Database** completely runs from the 8 NVMes configured in a software RAID-0, formatted with XFS. The usable capacity is **16TB**.

The **Results Database** completeley runs from the 10 SSDs configured in a software RAID-10, formatted with XFS. The usable capacity is **4TB**.

Both database clusters run in **continuous archive mode**, archiving WAL segments to the **Archive Storage**.

The **Work Database** is used for big ETLs and analytical workloads. Only final results are copied over to the **Results Database**. All *presentation* front-ends fetch data from the **Results Database**.

Pros:

* likely the highest performance setup we can achieve
* clear separation in "work" and "results" datasets
* each database can be tuned to needs (performance vs availability)
* **Work Database** maintainance/downtime does not affect presentation frontends

Cons:

* two database clusters required database links / foreign tables to move data between
* small risk of small data loss on **Work Database**


## Storage Configuration B

In this variant, a single PostgreSQL database cluster is run.

The 10 internal SSDs are configured in a software RAID-10 formatted with XFS and hold the primary database cluster area (`PGDATA`).

2 NVMe SSDs are configured in a software RAID-1 formatted with XFS and hold the transaction logs of the database (WAL segments, `PGDATA/pg_xlog`).

The remaining 6 NVMe SSDs are configured in a software RAID-0 formatted with XFS and hold an additional **FAST Tablespace** (`PGDATA/pg_tblspc/fast`).


## Results Database

To create the storage area for **Results Database**:

```console
mdadm --create /dev/md123 --name result --level=10 --chunk=256 --raid-devices=10 /dev/sd[b-c] /dev/sd[e-l]
```

This creates a complex RAID-10.

Another variant would be to create a nested RAID:

```console
mdadm --create /dev/md230 --name result0 --level=1 --raid-devices=2 /dev/sd{b,c}
mdadm --create /dev/md231 --name result1 --level=1 --raid-devices=2 /dev/sd{e,f}
mdadm --create /dev/md232 --name result2 --level=1 --raid-devices=2 /dev/sd{g,h}
mdadm --create /dev/md233 --name result3 --level=1 --raid-devices=2 /dev/sd{i,j}
mdadm --create /dev/md234 --name result4 --level=1 --raid-devices=2 /dev/sd{k,l}
mdadm --create /dev/md235 --name result --level=0 --raid-devices=5 /dev/md23[0-4]
```

Check settings:

```console
for drive in {a..l}; do cat /sys/block/sd${drive}/queue/scheduler; done
for drive in {a..l}; do cat /sys/block/sd${drive}/device/queue_depth; done
for drive in {a..l}; do cat /sys/block/sd${drive}/queue/add_random; done
for drive in {a..l}; do cat /sys/block/sd${drive}/queue/rq_affinity; done
for drive in {a..l}; do cat /sys/block/sd${drive}/queue/nr_requests; done
```

Adjust settings:

```console
for drive in {a..l}; do echo noop > /sys/block/sd${drive}/queue/scheduler; done
for drive in {a..l}; do echo 32 > /sys/block/sd${drive}/device/queue_depth; done
for drive in {a..l}; do echo 0 > /sys/block/sd${drive}/queue/add_random; done
for drive in {a..l}; do echo 1 > /sys/block/sd${drive}/queue/rq_affinity; done
```

To make these settings permanent, add above to `/etc/rc.d/boot.local`.


## Work Database

To create the storage area for **Work Database**:

```console
mdadm --create /dev/md124 --name work --level=0 --raid-devices=8 /dev/nvme[0-7]n1
```

Check NUMA assignment:

```console
for drive in {0..7}; do cat /sys/block/nvme${drive}n1/device/numa_node; done
```

Check settings:

```console
for drive in {0..7}; do cat /sys/block/nvme${drive}n1/queue/scheduler; done
for drive in {0..7}; do cat /sys/block/nvme${drive}n1/queue/add_random; done
for drive in {0..7}; do cat /sys/block/nvme${drive}n1/queue/rq_affinity; done
for drive in {0..7}; do cat /sys/block/nvme${drive}n1/queue/nr_requests; done
```

Adjust settings:

```console
for drive in {0..7}; do echo none > /sys/block/nvme${drive}n1/queue/scheduler; done
for drive in {0..7}; do echo 0 > /sys/block/nvme${drive}n1/queue/add_random; done
for drive in {0..7}; do echo 1 > /sys/block/nvme${drive}n1/queue/rq_affinity; done
```

To make these settings permanent, add above to `/etc/rc.d/boot.local`.


## Archive

The **Archive** storage subsystem is a 4U external JBOD with 24 [Seagate 6TB SAS (ST6000NM0014)](http://www.seagate.com/de/de/internal-hard-drives/nas-drives/enterprise-capacity-3-5-hdd/) magnetic disks.


### Reliability

The disks are designed for 24h operation in data-centers and have

* MTBF 2 Mio. hours
* AFR: 0,44 %
* UBER: 1 sector in every 10^15 bits read

The probability that at least 1 drive fails completely within 1 year is thus 1 - (1 - 0.0044)^24 = 10%.


### Disk Identification

The disks of the **Archive** subsystem are:

```console
bvr-sql18:~ # lsblk -io KNAME,TYPE,SIZE,MODEL | grep ST6000
sdm     disk    5,5T ST6000NM0014    
sdn     disk    5,5T ST6000NM0014    
sdo     disk    5,5T ST6000NM0014    
sdp     disk    5,5T ST6000NM0014    
sdq     disk    5,5T ST6000NM0014    
sdr     disk    5,5T ST6000NM0014    
sds     disk    5,5T ST6000NM0014    
sdt     disk    5,5T ST6000NM0014    
sdu     disk    5,5T ST6000NM0014    
sdv     disk    5,5T ST6000NM0014    
sdw     disk    5,5T ST6000NM0014    
sdx     disk    5,5T ST6000NM0014    
sdy     disk    5,5T ST6000NM0014    
sdz     disk    5,5T ST6000NM0014    
sdaa    disk    5,5T ST6000NM0014    
sdab    disk    5,5T ST6000NM0014    
sdac    disk    5,5T ST6000NM0014    
sdad    disk    5,5T ST6000NM0014    
sdae    disk    5,5T ST6000NM0014    
sdaf    disk    5,5T ST6000NM0014    
sdag    disk    5,5T ST6000NM0014    
sdah    disk    5,5T ST6000NM0014    
sdai    disk    5,5T ST6000NM0014    
sdaj    disk    5,5T ST6000NM0014    
```

To check their RAID status:

```console
bvr-sql18:~ # mdadm -E /dev/sd[m-z] /dev/sda[a-j]
mdadm: No md superblock detected on /dev/sdm.
mdadm: No md superblock detected on /dev/sdn.
mdadm: No md superblock detected on /dev/sdo.
mdadm: No md superblock detected on /dev/sdp.
mdadm: No md superblock detected on /dev/sdq.
mdadm: No md superblock detected on /dev/sdr.

mdadm: No md superblock detected on /dev/sds.
mdadm: No md superblock detected on /dev/sdt.
mdadm: No md superblock detected on /dev/sdu.
mdadm: No md superblock detected on /dev/sdv.
mdadm: No md superblock detected on /dev/sdw.
mdadm: No md superblock detected on /dev/sdx.

mdadm: No md superblock detected on /dev/sdy.
mdadm: No md superblock detected on /dev/sdz.
mdadm: No md superblock detected on /dev/sdaa.
mdadm: No md superblock detected on /dev/sdab.
mdadm: No md superblock detected on /dev/sdac.
mdadm: No md superblock detected on /dev/sdad.

mdadm: No md superblock detected on /dev/sdae.
mdadm: No md superblock detected on /dev/sdaf.
mdadm: No md superblock detected on /dev/sdag.
mdadm: No md superblock detected on /dev/sdah.
mdadm: No md superblock detected on /dev/sdai.
mdadm: No md superblock detected on /dev/sdaj.
```

### Delete Array


mdadm --misc --zero-superblock /dev/sd[m-z] /dev/sda[a-j]

### Entrpoy Source

By default, block devices are used as an entropy source (this is done by `/usr/sbin/haveged` which is running). Disable that:

```console
for drive in {m..z}; do echo 0 > /sys/block/sd${drive}/queue/add_random; done
for drive in {a..j}; do echo 0 > /sys/block/sda${drive}/queue/add_random; done
```

### IO Scheduler

Check current IO scheduer (should be `cfq`):

```console
for drive in {m..z}; do cat /sys/block/sd${drive}/queue/scheduler; done
for drive in {a..j}; do cat /sys/block/sda${drive}/queue/scheduler; done
```

Set IO scheduler to `cfq`:

```console
for drive in {m..z}; do echo cfq > /sys/block/sd${drive}/queue/scheduler; done
for drive in {a..j}; do echo cfq > /sys/block/sda${drive}/queue/scheduler; done
```


### Queue Depth

Check current queue depth setting (should be 32):

```console
for drive in {m..z}; do cat /sys/block/sd${drive}/device/queue_depth; done
for drive in {a..j}; do cat /sys/block/sda${drive}/device/queue_depth; done
```

Set queue depth to 32:

```console
for drive in {m..z}; do echo 32 > /sys/block/sd${drive}/device/queue_depth; done
for drive in {a..j}; do echo 32 > /sys/block/sda${drive}/device/queue_depth; done
```


### Creating the array

We will create a RAID-60 software RAID setup using the nesting feature of `mdadm'.

First, create the 4 RAID-6 set with 6 disks each:

```console
mdadm --create /dev/md240 --name archive0 --level=6 --raid-devices=6 /dev/sd[m-r]
mdadm --create /dev/md241 --name archive1 --level=6 --raid-devices=6 /dev/sd[s-x]
mdadm --create /dev/md242 --name archive2 --level=6 --raid-devices=6 /dev/sd[y-z] /dev/sda[a-d]
mdadm --create /dev/md243 --name archive3 --level=6 --raid-devices=6 /dev/sda[e-j]
```

Now create the RAID-0 from above RAID-6 sets:

```console
mdadm --create /dev/md244 --name archive --level=0 --raid-devices=4 /dev/md24[0-3]
```

Then create the XFS filesystem on top:

```console
mkfs.xfs /dev/md244
```

noatime,nodiratime,errors=remount-ro


#### Resources

* https://raid.wiki.kernel.org/index.php/RAID_setup
* https://www.suse.com/documentation/sles10/stor_admin/data/raidmdadmr6.html
* https://www.suse.com/documentation/sles10/stor_admin/data/raidmdadmr10nest.html


## PostgreSQL

PGDATA
PGDATA/pg_xlog
PGDATA/base/pgsql_tmp

Temporary files (for operations such as sorting more data than can fit in memory) are created within PGDATA/base/pgsql_tmp, or within a pgsql_tmp subdirectory of a tablespace directory if a tablespace other than pg_default is specified for them. 


http://www.postgresql.org/docs/9.4/static/storage-file-layout.html

https://lwn.net/Articles/590214/


##

To check the on-disk size of PostgreSQL tables:

```sql
SELECT
    relname,
    pg_relation_filepath(oid) filepath,
    round(relpages::numeric*8192./1024./1024./1024.,1) gbytes
FROM
    pg_class
WHERE
    relname LIKE 'tbl_%_201212'
ORDER BY
    3 DESC
;
```

Note that PostgreSQL may store data for a single table in multiple files. E.g.

```
relname                     filepath            gbytes
-------------------------------------------------------------
tbl_pk_konto_kkv_201212     base/20444/80072    5.2
```

is stored in multiple files:

```console
$ pwd
/usr/local/pgsql/data
$ ls -la base/20444/80072*
-rw-------  1 pgsql  pgsql  1073741824 Apr 10 15:42 base/20444/80072
-rw-------  1 pgsql  pgsql  1073741824 Apr 10 15:43 base/20444/80072.1
-rw-------  1 pgsql  pgsql  1073741824 Apr 10 15:43 base/20444/80072.2
-rw-------  1 pgsql  pgsql  1073741824 Apr 10 15:44 base/20444/80072.3
-rw-------  1 pgsql  pgsql  1073741824 Apr 10 15:45 base/20444/80072.4
-rw-------  1 pgsql  pgsql   264060928 Apr 13 13:42 base/20444/80072.5
-rw-------  1 pgsql  pgsql     1400832 Apr 10 15:35 base/20444/80072_fsm
```

# Final Configuration

md persistent configuration:

```console
bvr-sql18:~ # cat /etc/mdadm.conf
DEVICE containers partitions
ARRAY /dev/md/boot UUID=abd31c3e:314d868e:a76a42b2:6025b230
ARRAY /dev/md/root UUID=67221fe1:b542bd90:5f716fd9:f80f8014
ARRAY /dev/md/swap UUID=e726ac5a:34f5c549:534b092c:91913311
ARRAY /dev/md/work  metadata=1.2 UUID=f13a126b:791cb459:f9bf3f82:8c097359 name=bvr-sql18:work
ARRAY /dev/md/result  metadata=1.2 UUID=a4fe6ef1:73fa5f1c:208333bd:83d74343 name=bvr-sql18:result
ARRAY /dev/md/archive2  metadata=1.2 UUID=e9f51cea:ce6a492f:e592ccd2:9bdc7e6d name=bvr-sql18:archive2
ARRAY /dev/md/archive3  metadata=1.2 UUID=adbebc87:5016ce48:afd53e25:2358ec19 name=bvr-sql18:archive3
ARRAY /dev/md/archive1  metadata=1.2 UUID=69c90acd:6e7b1849:19f42f3a:bccc60c1 name=bvr-sql18:archive1
ARRAY /dev/md/archive0  metadata=1.2 UUID=5c2dad3a:5663346e:e3a5f304:7676615c name=bvr-sql18:archive0
ARRAY /dev/md/archive  metadata=1.2 UUID=1676a04e:49b84715:1bae00c5:f08e5d70 name=bvr-sql18:archive
```

md configuration:

```console
bvr-sql18:~ # cat /proc/mdstat
Personalities : [raid1] [raid0] [raid10] [raid6] [raid5] [raid4]
md243 : active raid6 sdaj[5] sdai[4] sdah[3] sdag[2] sdaf[1] sdae[0]
      23441565696 blocks super 1.2 level 6, 512k chunk, algorithm 2 [6/6] [UUUUUU]
      bitmap: 0/44 pages [0KB], 65536KB chunk

md242 : active raid6 sdad[5] sdac[4] sdab[3] sdaa[2] sdz[1] sdy[0]
      23441565696 blocks super 1.2 level 6, 512k chunk, algorithm 2 [6/6] [UUUUUU]
      bitmap: 0/44 pages [0KB], 65536KB chunk

md241 : active raid6 sdx[5] sdw[4] sdv[3] sdu[2] sdt[1] sds[0]
      23441565696 blocks super 1.2 level 6, 512k chunk, algorithm 2 [6/6] [UUUUUU]
      bitmap: 0/44 pages [0KB], 65536KB chunk

md121 : active raid0 md243[3] md242[2] md241[1] md240[0]
      93765738496 blocks super 1.2 512k chunks

md240 : active raid6 sdr[5] sdq[4] sdp[3] sdo[2] sdn[1] sdm[0]
      23441565696 blocks super 1.2 level 6, 512k chunk, algorithm 2 [6/6] [UUUUUU]
      bitmap: 0/44 pages [0KB], 65536KB chunk

md123 : active raid10 sdh[5] sdl[9] sdk[7] sdj[8] sdi[6] sdg[4] sdb[0] sdc[1] sde[2] sdf[3]
      3906405120 blocks super 1.2 256K chunks 2 near-copies [10/10] [UUUUUUUUUU]
      bitmap: 1/30 pages [4KB], 65536KB chunk

md124 : active raid0 nvme7n1[7] nvme6n1[6] nvme5n1[5] nvme4n1[4] nvme3n1[3] nvme2n1[2] nvme1n1[1] nvme0n1[0]
      15627067392 blocks super 1.2 512k chunks

md125 : active raid1 sdd2[1] sda2[0]
      20972416 blocks super 1.0 [2/2] [UU]
      bitmap: 0/1 pages [0KB], 65536KB chunk

md126 : active raid1 sda1[0] sdd1[1]
      1051584 blocks super 1.0 [2/2] [UU]
      bitmap: 0/1 pages [0KB], 65536KB chunk

md127 : active raid1 sdd3[1] sda3[0]
      759385920 blocks super 1.0 [2/2] [UU]
      bitmap: 0/6 pages [0KB], 65536KB chunk

unused devices: <none>
```

md array details:

```console
bvr-sql18:~ # mdadm --detail /dev/md/work
/dev/md/work:
        Version : 1.2
  Creation Time : Tue Apr 28 13:41:06 2015
     Raid Level : raid0
     Array Size : 15627067392 (14903.13 GiB 16002.12 GB)
   Raid Devices : 8
  Total Devices : 8
    Persistence : Superblock is persistent

    Update Time : Tue Apr 28 13:41:06 2015
          State : clean
 Active Devices : 8
Working Devices : 8
 Failed Devices : 0
  Spare Devices : 0

     Chunk Size : 512K

           Name : bvr-sql18:work  (local to host bvr-sql18)
           UUID : f13a126b:791cb459:f9bf3f82:8c097359
         Events : 0

    Number   Major   Minor   RaidDevice State
       0     259        0        0      active sync   /dev/nvme0n1
       1     259        1        1      active sync   /dev/nvme1n1
       2     259        2        2      active sync   /dev/nvme2n1
       3     259        3        3      active sync   /dev/nvme3n1
       4     259        4        4      active sync   /dev/nvme4n1
       5     259        5        5      active sync   /dev/nvme5n1
       6     259        6        6      active sync   /dev/nvme6n1
       7     259        7        7      active sync   /dev/nvme7n1
bvr-sql18:~ # mdadm --detail /dev/md/result
/dev/md/result:
        Version : 1.2
  Creation Time : Wed Apr 29 16:17:10 2015
     Raid Level : raid10
     Array Size : 3906405120 (3725.44 GiB 4000.16 GB)
  Used Dev Size : 781281024 (745.09 GiB 800.03 GB)
   Raid Devices : 10
  Total Devices : 10
    Persistence : Superblock is persistent

  Intent Bitmap : Internal

    Update Time : Thu Apr 30 15:54:11 2015
          State : active
 Active Devices : 10
Working Devices : 10
 Failed Devices : 0
  Spare Devices : 0

         Layout : near=2
     Chunk Size : 256K

           Name : bvr-sql18:result  (local to host bvr-sql18)
           UUID : a4fe6ef1:73fa5f1c:208333bd:83d74343
         Events : 3400

    Number   Major   Minor   RaidDevice State
       0       8       16        0      active sync set-A   /dev/sdb
       1       8       32        1      active sync set-B   /dev/sdc
       2       8       64        2      active sync set-A   /dev/sde
       3       8       80        3      active sync set-B   /dev/sdf
       4       8       96        4      active sync set-A   /dev/sdg
       5       8      112        5      active sync set-B   /dev/sdh
       6       8      128        6      active sync set-A   /dev/sdi
       7       8      160        7      active sync set-B   /dev/sdk
       8       8      144        8      active sync set-A   /dev/sdj
       9       8      176        9      active sync set-B   /dev/sdl
bvr-sql18:~ # mdadm --detail /dev/md/archive
/dev/md/archive:
        Version : 1.2
  Creation Time : Tue Apr 28 13:10:46 2015
     Raid Level : raid0
     Array Size : 93765738496 (89421.98 GiB 96016.12 GB)
   Raid Devices : 4
  Total Devices : 4
    Persistence : Superblock is persistent

    Update Time : Tue Apr 28 13:10:46 2015
          State : clean
 Active Devices : 4
Working Devices : 4
 Failed Devices : 0
  Spare Devices : 0

     Chunk Size : 512K

           Name : bvr-sql18:archive  (local to host bvr-sql18)
           UUID : 1676a04e:49b84715:1bae00c5:f08e5d70
         Events : 0

    Number   Major   Minor   RaidDevice State
       0       9      240        0      active sync   /dev/md240
       1       9      241        1      active sync   /dev/md241
       2       9      242        2      active sync   /dev/md242
       3       9      243        3      active sync   /dev/md243
bvr-sql18:~ # mdadm --detail /dev/md240
/dev/md240:
        Version : 1.2
  Creation Time : Tue May  5 10:47:56 2015
     Raid Level : raid6
     Array Size : 23441565696 (22355.62 GiB 24004.16 GB)
  Used Dev Size : 5860391424 (5588.90 GiB 6001.04 GB)
   Raid Devices : 6
  Total Devices : 6
    Persistence : Superblock is persistent

  Intent Bitmap : Internal

    Update Time : Wed May  6 12:30:27 2015
          State : active
 Active Devices : 6
Working Devices : 6
 Failed Devices : 0
  Spare Devices : 0

         Layout : left-symmetric
     Chunk Size : 512K

           Name : bvr-sql18:archive0  (local to host bvr-sql18)
           UUID : 5c2dad3a:5663346e:e3a5f304:7676615c
         Events : 18784

    Number   Major   Minor   RaidDevice State
       0       8      192        0      active sync   /dev/sdm
       1       8      208        1      active sync   /dev/sdn
       2       8      224        2      active sync   /dev/sdo
       3       8      240        3      active sync   /dev/sdp
       4      65        0        4      active sync   /dev/sdq
       5      65       16        5      active sync   /dev/sdr
bvr-sql18:~ # mdadm --detail /dev/md241
/dev/md241:
        Version : 1.2
  Creation Time : Tue May  5 10:48:01 2015
     Raid Level : raid6
     Array Size : 23441565696 (22355.62 GiB 24004.16 GB)
  Used Dev Size : 5860391424 (5588.90 GiB 6001.04 GB)
   Raid Devices : 6
  Total Devices : 6
    Persistence : Superblock is persistent

  Intent Bitmap : Internal

    Update Time : Wed May  6 12:39:45 2015
          State : active
 Active Devices : 6
Working Devices : 6
 Failed Devices : 0
  Spare Devices : 0

         Layout : left-symmetric
     Chunk Size : 512K

           Name : bvr-sql18:archive1  (local to host bvr-sql18)
           UUID : 69c90acd:6e7b1849:19f42f3a:bccc60c1
         Events : 18896

    Number   Major   Minor   RaidDevice State
       0      65       32        0      active sync   /dev/sds
       1      65       48        1      active sync   /dev/sdt
       2      65       64        2      active sync   /dev/sdu
       3      65       80        3      active sync   /dev/sdv
       4      65       96        4      active sync   /dev/sdw
       5      65      112        5      active sync   /dev/sdx
bvr-sql18:~ # mdadm --detail /dev/md242
/dev/md242:
        Version : 1.2
  Creation Time : Tue May  5 10:48:09 2015
     Raid Level : raid6
     Array Size : 23441565696 (22355.62 GiB 24004.16 GB)
  Used Dev Size : 5860391424 (5588.90 GiB 6001.04 GB)
   Raid Devices : 6
  Total Devices : 6
    Persistence : Superblock is persistent

  Intent Bitmap : Internal

    Update Time : Wed May  6 12:58:11 2015
          State : active
 Active Devices : 6
Working Devices : 6
 Failed Devices : 0
  Spare Devices : 0

         Layout : left-symmetric
     Chunk Size : 512K

           Name : bvr-sql18:archive2  (local to host bvr-sql18)
           UUID : e9f51cea:ce6a492f:e592ccd2:9bdc7e6d
         Events : 19120

    Number   Major   Minor   RaidDevice State
       0      65      128        0      active sync   /dev/sdy
       1      65      144        1      active sync   /dev/sdz
       2      65      160        2      active sync   /dev/sdaa
       3      65      176        3      active sync   /dev/sdab
       4      65      192        4      active sync   /dev/sdac
       5      65      208        5      active sync   /dev/sdad
bvr-sql18:~ # mdadm --detail /dev/md243
/dev/md243:
        Version : 1.2
  Creation Time : Tue May  5 10:48:15 2015
     Raid Level : raid6
     Array Size : 23441565696 (22355.62 GiB 24004.16 GB)
  Used Dev Size : 5860391424 (5588.90 GiB 6001.04 GB)
   Raid Devices : 6
  Total Devices : 6
    Persistence : Superblock is persistent

  Intent Bitmap : Internal

    Update Time : Wed May  6 13:06:36 2015
          State : active
 Active Devices : 6
Working Devices : 6
 Failed Devices : 0
  Spare Devices : 0

         Layout : left-symmetric
     Chunk Size : 512K

           Name : bvr-sql18:archive3  (local to host bvr-sql18)
           UUID : adbebc87:5016ce48:afd53e25:2358ec19
         Events : 19222

    Number   Major   Minor   RaidDevice State
       0      65      224        0      active sync   /dev/sdae
       1      65      240        1      active sync   /dev/sdaf
       2      66        0        2      active sync   /dev/sdag
       3      66       16        3      active sync   /dev/sdah
       4      66       32        4      active sync   /dev/sdai
       5      66       48        5      active sync   /dev/sdaj
bvr-sql18:~ #
```

Filesystem configuration:

```console
bvr-sql18:~ # cat /etc/fstab
UUID=90ce80d6-c110-4148-9aa6-cd2896b49469 swap swap defaults 0 0
UUID=1a6b8cd8-3bfd-440e-bf9e-539199d38e50 / btrfs defaults 0 0
UUID=1a6b8cd8-3bfd-440e-bf9e-539199d38e50 /home btrfs subvol=@/home 0 0
UUID=1a6b8cd8-3bfd-440e-bf9e-539199d38e50 /opt btrfs subvol=@/opt 0 0
UUID=1a6b8cd8-3bfd-440e-bf9e-539199d38e50 /srv btrfs subvol=@/srv 0 0
UUID=1a6b8cd8-3bfd-440e-bf9e-539199d38e50 /tmp btrfs subvol=@/tmp 0 0
UUID=1a6b8cd8-3bfd-440e-bf9e-539199d38e50 /usr/local btrfs subvol=@/usr/local 0 0
UUID=1a6b8cd8-3bfd-440e-bf9e-539199d38e50 /var/crash btrfs subvol=@/var/crash 0 0
UUID=1a6b8cd8-3bfd-440e-bf9e-539199d38e50 /var/lib/mailman btrfs subvol=@/var/lib/mailman 0 0
UUID=1a6b8cd8-3bfd-440e-bf9e-539199d38e50 /var/lib/named btrfs subvol=@/var/lib/named 0 0
UUID=1a6b8cd8-3bfd-440e-bf9e-539199d38e50 /var/lib/pgsql btrfs subvol=@/var/lib/pgsql 0 0
UUID=1a6b8cd8-3bfd-440e-bf9e-539199d38e50 /var/log btrfs subvol=@/var/log 0 0
UUID=1a6b8cd8-3bfd-440e-bf9e-539199d38e50 /var/opt btrfs subvol=@/var/opt 0 0
UUID=1a6b8cd8-3bfd-440e-bf9e-539199d38e50 /var/spool btrfs subvol=@/var/spool 0 0
UUID=1a6b8cd8-3bfd-440e-bf9e-539199d38e50 /var/tmp btrfs subvol=@/var/tmp 0 0
UUID=bafc16b7-74c0-4d54-9976-eeb349c6fb62 /boot ext4 acl,user_xattr 1 2
UUID=1a6b8cd8-3bfd-440e-bf9e-539199d38e50 /.snapshots btrfs subvol=@/.snapshots 0 0

UUID=116f1cc2-74d2-44a7-b4e2-e8196bc86d82 /data/work xfs noatime,nodiratime 0 0
```

# Backup and Recovery

The starting point can only be a business requirement and it is defined through the concept of retention policy.
 Usually, a company defines a disaster recovery plan within a business continuity plan, where it is clearly defined the period of retention of backup data. In the same documents we find both the recovery point objective (RPO) and the recovery time objective (RTO) definitions, the two key metrics that respectively measure the amount of data that a business can afford to lose and the maximum allowed time to recover from a disaster.

In a perfect world, there would be no need for a backup. However it is important, especially in business environments, to be prepared for when the "unexpected" happens. In a database scenario, the unexpected could take any of the following forms:

* data corruption
* system failure, including hardware failure
* human error
* natural disaster

For now, you should be aware that any PostgreSQL physical/binary backup (not to be confused with the logical backups produced by the pg_dump utility) is composed of:

* a base backup; 
* one or more WAL files (usually collected through continuous archiving). 


https://github.com/wal-e/wal-e
https://developer.rackspace.com/blog/postgresql-plus-wal-e-plus-cloudfiles-equals-awesome/
http://www.hagander.net/talks/Backup%20strategies.pdf
http://riaschissl.bestsolution.at/2015/03/repair-corrupt-tar-archives-the-better-way/



**Weekly, full, logical backups**
`
Building OpenSSL from source:

```console
cd ~
wget https://www.openssl.org/source/openssl-1.0.2c.tar.gz
tar xvzf openssl-1.0.2c.tar.gz
cd openssl-1.0.2c
config --prefix=$HOME/openssl
make
make install
export OPENSSL_CONF=/etc/ssl/openssl.cnf
```

Performance of the system OpenSSL at SHA256

```console
postgres@bvr-sql18:/data/archive/adr_work> time /usr/bin/openssl sha256 /data/archive/adr_work/backup_sql18_adr_work_20160622/24029.dat.gz
SHA256(/data/archive/adr_work/backup_sql18_adr_work_20160622/24029.dat.gz)= 24ec7703a28defe0dedcc09a3ac792900b5cbaf79d6e64e212f643e7684be2a7

real    0m3.376s
user    0m2.828s
sys     0m0.544s
```

Performance of custom built OpenSSL at SHA256:

```console
postgres@bvr-sql18:/data/archive/adr_work> time /home/oberstet/openssl/bin/openssl sha256 /data/archive/adr_work/backup_sql18_adr_work_20160622/24029.dat.gz
SHA256(/data/archive/adr_work/backup_sql18_adr_work_20160622/24029.dat.gz)= 24ec7703a28defe0dedcc09a3ac792900b5cbaf79d6e64e212f643e7684be2a7

real    0m2.659s
user    0m1.928s
sys     0m0.728s
```

"The dump duration has no effect on dump integrity. Integrity is ensured by using one transaction
with repeatable read isolation level by all pg_dump process. There are NO table write locks."
http://www.postgresql.org/docs/current/static/transaction-iso.html#XACT-REPEATABLE-READ

"pg_dump, the PostgreSQL dump utility, starts it job with issuing SET TRANSACTION ISOLATION LEVEL SERIALIZABLE,
to guarantee that the state of database being dumped would be that of the moment the utility was run,
and the subsequent changes to the database could not interfere with the dump."
http://stackoverflow.com/a/5729386

Performing a full, logical backup of the database using 16 parallel workers took **<5 hours** (with almost no system activity other than the backup):

```console
postgres@bvr-sql18:~/data> time pg_dump -Fd -j 16 -f /data/archive/adr_work/backup_sql18_adr_work_20160622 adr

real    261m57.490s
user    1290m5.744s
sys     35m5.512s
```

The full backup consists of 2500 files and 550GB:

```console
bvr-sql18:/home/oberstet # find /data/archive/adr_work/backup_sql18_adr_work_20160622/ | wc -l
2360
bvr-sql18:/home/oberstet # du -hs /data/archive/adr_work/backup_sql18_adr_work_20160622/
543G    /data/archive/adr_work/backup_sql18_adr_work_20160622/
```

Creating a tar archive took 30 minutes:

```console
bvr-sql18:/data/archive/adr_work # time tar -cf backup_sql18_adr_work_20160622.tar backup_sql18_adr_work_20160622

real    31m40.619s
user    0m6.620s
sys     13m53.636s
```

Create a log file with SHA256 fingerprints

```console
bvr-sql18:/data/archive/adr_work # time find /data/archive/adr_work/backup_sql18_adr_work_20160622/ -type f -exec openssl sha256 {} \; > backup_sql18_adr_work_20160622.log

real    42m43.522s
user    33m44.980s
sys     7m55.192s
```

Create SHA256 fingerprint for tar archive:

```console
bvr-sql18:/data/archive/adr_work # time openssl sha256 backup_sql18_adr_work_20160622.tar
SHA256(backup_sql18_adr_work_20160622.tar)= b9f8dddf1c71c13d62a9f591d4b70961a50b309c31e0d9187f1754559f4b6ce5

real    42m22.338s
user    32m43.436s
sys     7m51.496s
```

**Continuous archiving of WAL files through shipping**
  
PostgreSQL 9.4 introduced the [pg_stat_archiver](http://blog.2ndquadrant.com/monitoring-wal-archiving-improves-postgresql-9-4-pg_stat_archiver/) **system view**
which provides information on the WAL archival process.

## Work Database

The **Work Database** is the primary database for running ETL, analytical and statistical workloads.

This database resides on a RAID-0 NVMe SSD array with a net capacity of 15TB.

[Continuous Archiving](http://www.postgresql.org/docs/9.4/static/continuous-archiving.html)

`/var/lib/pgsql/data/postgresql.conf`


[WAL level](http://www.postgresql.org/docs/9.4/static/runtime-config-wal.html#GUC-WAL-LEVEL) must be set to `archive`.
[Archive mode](http://www.postgresql.org/docs/9.4/static/runtime-config-wal.html#GUC-ARCHIVE-MODE) must be enabled.

```
wal_level = archive
archive_mode = on
archive_command = 'test ! -f /mnt/server/archivedir/%f && cp %p /mnt/server/archivedir/%f'  # Unix
archive_timeout = 300
```

# NVMe

## Related Mailing Lists

* http://lists.infradead.org/mailman/listinfo/linux-nvme


## Info

Find Intel NVMe PCIe cards:

```console
root@bvr-sql18:~# lspci | grep "Non-Volatile memory controller"
41:00.0 Non-Volatile memory controller: Intel Corporation Device 0953 (rev 01)
43:00.0 Non-Volatile memory controller: Intel Corporation Device 0953 (rev 01)
45:00.0 Non-Volatile memory controller: Intel Corporation Device 0953 (rev 01)
81:00.0 Non-Volatile memory controller: Intel Corporation Device 0953 (rev 01)
83:00.0 Non-Volatile memory controller: Intel Corporation Device 0953 (rev 01)
84:00.0 Non-Volatile memory controller: Intel Corporation Device 0953 (rev 01)
c1:00.0 Non-Volatile memory controller: Intel Corporation Device 0953 (rev 01)
c2:00.0 Non-Volatile memory controller: Intel Corporation Device 0953 (rev 01)
```

Show details for a single card:

```console
root@bvr-sql18:~# lspci -s 41:00.0 -v
41:00.0 Non-Volatile memory controller: Intel Corporation Device 0953 (rev 01) (prog-if 02 [NVM Express])
        Subsystem: Intel Corporation Device 3702
        Physical Slot: 3
        Flags: bus master, fast devsel, latency 0, IRQ 33
        Memory at c6010000 (64-bit, non-prefetchable) [size=16K]
        Expansion ROM at c6000000 [disabled] [size=64K]
        Capabilities: [40] Power Management version 3
        Capabilities: [50] MSI-X: Enable+ Count=32 Masked-
        Capabilities: [60] Express Endpoint, MSI 00
        Capabilities: [100] Advanced Error Reporting
        Capabilities: [150] Virtual Channel
        Capabilities: [180] Power Budgeting <?>
        Capabilities: [190] Alternative Routing-ID Interpretation (ARI)
        Capabilities: [270] Device Serial Number 55-cd-2e-40-4b-e8-29-e4
        Capabilities: [2a0] #19
        Kernel driver in use: nvme
```

Show insane amount of details:

```console
root@bvr-sql18:~# lspci -s 41:00.0 -vvv
41:00.0 Non-Volatile memory controller: Intel Corporation Device 0953 (rev 01) (prog-if 02 [NVM Express])
        Subsystem: Intel Corporation Device 3702
        Physical Slot: 3
        Control: I/O- Mem+ BusMaster+ SpecCycle- MemWINV- VGASnoop- ParErr+ Stepping- SERR+ FastB2B- DisINTx+
        Status: Cap+ 66MHz- UDF- FastB2B- ParErr- DEVSEL=fast >TAbort- <TAbort- <MAbort- >SERR- <PERR- INTx-
        Latency: 0, Cache Line Size: 32 bytes
        Interrupt: pin A routed to IRQ 33
        Region 0: Memory at c6010000 (64-bit, non-prefetchable) [size=16K]
        Expansion ROM at c6000000 [disabled] [size=64K]
        Capabilities: [40] Power Management version 3
                Flags: PMEClk- DSI- D1- D2- AuxCurrent=0mA PME(D0-,D1-,D2-,D3hot-,D3cold-)
                Status: D0 NoSoftRst+ PME-Enable- DSel=0 DScale=0 PME-
        Capabilities: [50] MSI-X: Enable+ Count=32 Masked-
                Vector table: BAR=0 offset=00002000
                PBA: BAR=0 offset=00003000
        Capabilities: [60] Express (v2) Endpoint, MSI 00
                DevCap: MaxPayload 256 bytes, PhantFunc 0, Latency L0s <4us, L1 <4us
                        ExtTag+ AttnBtn- AttnInd- PwrInd- RBE+ FLReset+
                DevCtl: Report errors: Correctable+ Non-Fatal+ Fatal+ Unsupported-
                        RlxdOrd- ExtTag- PhantFunc- AuxPwr- NoSnoop+ FLReset-
                        MaxPayload 256 bytes, MaxReadReq 512 bytes
                DevSta: CorrErr+ UncorrErr- FatalErr- UnsuppReq+ AuxPwr- TransPend-
                LnkCap: Port #0, Speed 8GT/s, Width x4, ASPM L0s L1, Exit Latency L0s <4us, L1 <4us
                        ClockPM- Surprise- LLActRep- BwNot-
                LnkCtl: ASPM Disabled; RCB 64 bytes Disabled- CommClk-
                        ExtSynch- ClockPM- AutWidDis- BWInt- AutBWInt-
                LnkSta: Speed 8GT/s, Width x4, TrErr- Train- SlotClk- DLActive- BWMgmt- ABWMgmt-
                DevCap2: Completion Timeout: Range ABCD, TimeoutDis+, LTR-, OBFF Not Supported
                DevCtl2: Completion Timeout: 50us to 50ms, TimeoutDis-, LTR-, OBFF Disabled
                LnkCtl2: Target Link Speed: 8GT/s, EnterCompliance- SpeedDis-
                         Transmit Margin: Normal Operating Range, EnterModifiedCompliance- ComplianceSOS-
                         Compliance De-emphasis: -6dB
                LnkSta2: Current De-emphasis Level: -6dB, EqualizationComplete+, EqualizationPhase1+
                         EqualizationPhase2+, EqualizationPhase3+, LinkEqualizationRequest-
        Capabilities: [100 v1] Advanced Error Reporting
                UESta:  DLP- SDES- TLP- FCP- CmpltTO- CmpltAbrt- UnxCmplt- RxOF- MalfTLP- ECRC- UnsupReq- ACSViol-
                UEMsk:  DLP- SDES- TLP- FCP- CmpltTO- CmpltAbrt- UnxCmplt- RxOF- MalfTLP- ECRC- UnsupReq- ACSViol-
                UESvrt: DLP+ SDES+ TLP- FCP+ CmpltTO- CmpltAbrt- UnxCmplt- RxOF+ MalfTLP+ ECRC- UnsupReq- ACSViol-
                CESta:  RxErr- BadTLP- BadDLLP- Rollover- Timeout- NonFatalErr+
                CEMsk:  RxErr- BadTLP- BadDLLP- Rollover- Timeout- NonFatalErr+
                AERCap: First Error Pointer: 00, GenCap+ CGenEn- ChkCap+ ChkEn-
        Capabilities: [150 v1] Virtual Channel
                Caps:   LPEVC=0 RefClk=100ns PATEntryBits=1
                Arb:    Fixed- WRR32- WRR64- WRR128-
                Ctrl:   ArbSelect=Fixed
                Status: InProgress-
                VC0:    Caps:   PATOffset=00 MaxTimeSlots=1 RejSnoopTrans-
                        Arb:    Fixed- WRR32- WRR64- WRR128- TWRR128- WRR256-
                        Ctrl:   Enable+ ID=0 ArbSelect=Fixed TC/VC=01
                        Status: NegoPending- InProgress-
        Capabilities: [180 v1] Power Budgeting <?>
        Capabilities: [190 v1] Alternative Routing-ID Interpretation (ARI)
                ARICap: MFVC- ACS-, Next Function: 0
                ARICtl: MFVC- ACS-, Function Group: 0
        Capabilities: [270 v1] Device Serial Number 55-cd-2e-40-4b-e8-29-e4
        Capabilities: [2a0 v1] #19
        Kernel driver in use: nvme
```

Show NVMe kernel driver details:

```console
root@bvr-sql18:~# modinfo nvme
filename:       /lib/modules/3.19.0-15-generic/kernel/drivers/block/nvme.ko
version:        1.0
license:        GPL
author:         Matthew Wilcox <willy@linux.intel.com>
srcversion:     14567DC6FC941C827D9D73A
alias:          pci:v*d*sv*sd*bc01sc08i02*
depends:
intree:         Y
vermagic:       3.19.0-15-generic SMP mod_unload modversions
signer:         Magrathea: Glacier signing key
sig_key:        9E:64:80:70:92:F3:A6:A8:F6:6F:3B:7E:A4:CB:37:67:FD:FA:E0:8A
sig_hashalgo:   sha512
parm:           admin_timeout:timeout in seconds for admin commands (byte)
parm:           io_timeout:timeout in seconds for I/O (byte)
parm:           retry_time:time in seconds to retry failed I/O (byte)
parm:           shutdown_timeout:timeout in seconds for controller shutdown (byte)
parm:           nvme_major:int
parm:           use_threaded_interrupts:int
```

List NVMe devices and partitions:

```console
root@bvr-sql18:~# cat /proc/partitions | grep nvme
 259        0 1953514584 nvme0n1
 259        1 1953514584 nvme1n1
 259        2 1953514584 nvme2n1
 259        3 1953514584 nvme3n1
 259        4 1953514584 nvme4n1
 259        5 1953514584 nvme5n1
 259        6 1953514584 nvme6n1
 259        7 1953514584 nvme7n1
```

