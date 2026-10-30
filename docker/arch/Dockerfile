FROM archlinux:base

# Keep tools shared by all Arch builds here. Recipe-specific tools belong in makedepends.
RUN pacman -Syu --needed --noconfirm base-devel git namcap \
    && rm -f /var/cache/pacman/pkg/* \
    && useradd --create-home builder \
    && printf 'builder ALL=(root) NOPASSWD: /usr/bin/pacman\n' > /etc/sudoers.d/builder \
    && chmod 0440 /etc/sudoers.d/builder \
    && printf '\nOPTIONS+=(!debug)\n' >> /etc/makepkg.conf \
    && mkdir /build /output

COPY build /usr/local/bin/build-package
WORKDIR /build
ENTRYPOINT ["/bin/bash", "/usr/local/bin/build-package"]
