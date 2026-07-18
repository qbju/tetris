#include <inttypes.h>

#include <stdlib.h>
#include <stdbool.h>
#include <stdio.h>
#include <string.h>
#include <lfortran_intrinsics.h>


struct dimension_descriptor
{
    int32_t lower_bound, length, stride;
};

struct i32
{
    int32_t *data;
    struct dimension_descriptor dims[32];
    int32_t n_dims;
    int32_t offset;
    bool is_allocated;
};

int32_t _lcompilers_optimization_floordiv_i327(int32_t a, int32_t b);



// Implementations
int32_t _lcompilers_optimization_floordiv_i327(int32_t a, int32_t b)
{
    double r;
    int32_t result;
    int64_t tmp;
    r = (double)(a)/(double)(b);
    tmp = (int64_t)(r);
    if (r <   0.00000000000000000e+00 && (double)(tmp) != r) {
        tmp = tmp - 1;
    }
    result = tmp;
    return result;
}

int32_t __lpython_overloaded_2___mod(int32_t a, int32_t b)
{
    int32_t _lpython_return_variable;
    _lpython_return_variable = a - _lcompilers_optimization_floordiv_i327(a, b)*b;
    return _lpython_return_variable;
}

struct i32* board;
int32_t game_over = 0;
int32_t kind = 0;
int32_t next_kind = 1;
int32_t piece_x = 3;
int32_t piece_y = 0;
int32_t rotation = 0;
int32_t score = 0;
int32_t ticks = 0;
int32_t keyboard_scancode();

void ui_put_cell(int32_t x, int32_t y, int32_t glyph, int32_t colour);

int main(int argc, char* argv[])
{
    _lpython_set_argv(argc, argv);
    return 0;
}
