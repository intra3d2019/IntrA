#include <stdio.h>
#include <math.h>
#include <stdlib.h>


float path_distance(float* path, int length)
{
    float dis = 0.0;

    for (int i = 0; i < length - 3; i += 3) {
        dis += sqrt(powf(path[i] - path[i+3], 2) + powf(path[i+1] - path[i+4], 2) + powf(path[i+2] - path[i+5], 2));
    }

    return dis;
}