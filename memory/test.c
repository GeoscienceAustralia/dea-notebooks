#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

int main()
{
    int i, n = 1024*1024*1024;
    char *ptr;
    printf("Hello world\n");
    sleep(1);
    ptr = malloc(n); // request one gigabyte
    sleep(1);
    if (ptr == NULL) { printf("Fail."); return 1; }
    for (i = 0; i < n; i++) ptr[i] = 0; // write entire area
    sleep(1);
    free(ptr); // release
    sleep(1);
}