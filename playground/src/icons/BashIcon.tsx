import {rem} from '@mantine/core';

interface AddressBookIconProps extends React.ComponentPropsWithoutRef<'svg'> {
    size?: number | string;
}

export function BashIcon({size, style, ...others}: AddressBookIconProps) {
    return (
        <img
            style={{width: rem(size), height: rem(size), color: "white", ...style}}
            src="/static/bash.svg"
        />
    );
}

export default BashIcon;