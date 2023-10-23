import {rem} from '@mantine/core';

interface AddressBookIconProps extends React.ComponentPropsWithoutRef<'svg'> {
    size?: number | string;
}

export function BambooIcon({size, style, ...others}: AddressBookIconProps) {
    return (
        <img
            style={{width: rem(size), height: rem(size), ...style}}
            src="/static/bamboo.svg"
            alt="Bamboo"
        />
    );
}

export default BambooIcon;