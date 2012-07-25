/*!
  \file
  \brief リングバッファ

  \author Satofumi KAMIMURA

  $Id: ring_buffer.c 1811 2010-04-30 16:12:05Z satofumi $
*/

#include "ring_buffer.h"


void ring_initialize(ringBuffer_t *ring, char *buffer, const int shift_length)
{
    ring->buffer = buffer;
    ring->buffer_size = 1 << shift_length;
    ring_clear(ring);
}


void ring_clear(ringBuffer_t *ring)
{
    ring->first = 0;
    ring->last = 0;
}


int ring_size(const ringBuffer_t *ring)
{
    int first = ring->first;
    int last = ring->last;

    return (last >= first) ? last - first : ring->buffer_size - (first - last);
}


int ring_capacity(const ringBuffer_t *ring)
{
    return ring->buffer_size - 1;
}


static void charmove(char *dest, const char *src, int n)
{
    const char *last_p = dest + n;
    while (dest < last_p) {
        *dest++ = *src++;
    }
}


int ring_write(ringBuffer_t *ring, const char *data, int size)
{
    int free_size = ring_capacity(ring) - ring_size(ring);
    int push_size = (size > free_size) ? free_size : size;

    // データ配置
    if (ring->first <= ring->last) {
        // last から buffer_size 終端までに配置
        int left_size = 0;
        int to_end = ring->buffer_size - ring->last;
        int move_size = (to_end > push_size) ? push_size : to_end;

        charmove(&ring->buffer[ring->last], data, move_size);
        ring->last += move_size;
        ring->last &= (ring->buffer_size -1);

        left_size = push_size - move_size;
        if (left_size > 0) {
            // 0 から first の前までを配置
            charmove(ring->buffer, &data[move_size], left_size);
            ring->last = left_size;
        }
    } else {
        // last から first の前まで配置
        charmove(&ring->buffer[ring->last], data, size);
        ring->last += push_size;
    }
    return push_size;
}


int ring_read(ringBuffer_t *ring, char *buffer, int size)
{
    // データ取得
    int now_size = ring_size(ring);
    int pop_size = (size > now_size) ? now_size : size;

    if (ring->first <= ring->last) {
        charmove(buffer, &ring->buffer[ring->first], pop_size);
        ring->first += pop_size;

    } else {
        // first から buffer_size 終端までを配置
        int left_size = 0;
        int to_end = ring->buffer_size - ring->first;
        int move_size = (to_end > pop_size) ? pop_size : to_end;
        charmove(buffer, &ring->buffer[ring->first], move_size);

        ring->first += move_size;
        ring->first &= (ring->buffer_size -1);

        left_size = pop_size - move_size;
        if (left_size > 0) {
            // 0 から last の前までを配置
            charmove(&buffer[move_size], ring->buffer, left_size);

            ring->first = left_size;
        }
    }
    return pop_size;
}
