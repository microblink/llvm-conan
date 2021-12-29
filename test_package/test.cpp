#include <cstdint>
#include <iostream>
#include <stdexcept>
#include <variant>

#ifndef _LIBCPP_VERSION
#error "Not using libc++"
#endif

enum struct Foo : std::uint8_t
{
    First = 0,
    Second
};

enum struct Bar : std::uint8_t
{
    First = 0,
    Second
};

using S = std::variant< Foo, Bar >;

// template< std::size_t bla >
// struct print_size;

// print_size< sizeof( S ) > b;

// static_assert( sizeof( S ) == 2 );

int check( S const & bla )
{
    if ( std::holds_alternative< Bar >( bla ) )
    {
        throw std::invalid_argument( "wrong alternative!" );
    }
    return 0;
}

int main()
{
    std::cout << "Hello, world!" << std::endl;
    S bla = Foo::First;
    return check( bla );
}
