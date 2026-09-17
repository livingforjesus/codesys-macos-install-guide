#include <stddef.h>
void decode(unsigned char *p,size_t n,const unsigned char *k,size_t l){for(size_t i=0;i<n;i++)p[i]=~(k[(i%1024)%l]^((p[i]<<4)|(p[i]>>4)));}
