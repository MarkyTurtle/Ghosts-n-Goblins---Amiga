#include "stdafx.h"
#include <stdio.h>
#include <string.h>


int main(int c,char**v){
 CAPSInit(); int id=CAPSAddImage();
 if(CAPSLockImage(id,v[1])) {puts("lock fail");return 1;}
 CapsImageInfo ii; CAPSGetImageInfo(&ii,id);
 printf("cyl %u-%u heads %u-%u\n",ii.mincylinder,ii.maxcylinder,ii.minhead,ii.maxhead);
 CAPSLoadImage(id,DI_LOCK_DENVAR|DI_LOCK_TRKBIT|DI_LOCK_INDEX);
 for(unsigned cy=ii.mincylinder;cy<=ii.maxcylinder;cy++)for(unsigned h=ii.minhead;h<=ii.maxhead;h++){
  CapsTrackInfoT2 ti; memset(&ti,0,sizeof ti); ti.type=2;
  int r=CAPSLockTrack(&ti,id,cy,h,DI_LOCK_DENVAR|DI_LOCK_TRKBIT|DI_LOCK_INDEX|DI_LOCK_TYPE);
  char fn[64]; sprintf(fn,"%s/t%03u.bin",v[2],cy*2+h);
  FILE*f=fopen(fn,"wb"); if(!r&&ti.trackbuf) fwrite(ti.trackbuf,1,(ti.tracklen+7)/8,f); fclose(f);
  printf("%03u r=%d bits=%u weak=%u\n",cy*2+h,r,ti.tracklen,ti.weakcnt);
 }}
